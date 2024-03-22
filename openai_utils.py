from openai import OpenAI
import os
import time
class LLM_openai():
    def __init__(self, logger):
        self.client = OpenAI()
        self.logger = logger
        self.thread_id = None
    
    def log(self, content):
        self.logger.straight_write('conversation', content, mode='a')

    def load_assistant(self, asst_id):
        self.asst_id = asst_id
        self.assistant = self.client.beta.assistants.retrieve(asst_id)
        self.log(f'>> Loaded OpenAI assistant {self.asst_id}')

    def delete_thread(self):
        if self.thread_id is None:
            return
        response = self.client.beta.threads.delete(self.thread_id)
        assert response.deleted
        self.thread_id = None

    def chat(self, content, system_instruct = None, model="gpt-4-1106-preview", **kwargs):
        ''' 
        Output:
            - run_result
            - responce
            - files
        '''
        # init
        self.delete_thread()
        if system_instruct is None:
            system_instruct = 'You are an excellently helpful AI assistant for analysis and abstraction on data.'

        # chat
        completions = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instruct},
                {"role": "user", "content": content}
            ],
            **kwargs
        )
        print(completions.id)
        self.log( ('-' * 5) + f'{completions.id}' + ('-' * 10))
        self.log('User: \n' + content)

        
        # get responce
        responce = completions.choices[0].message.content
        self.log('ChatGPT: \n' + responce)
        
        return responce
    
    def chat_assistant(self, content, args, file_ids = []):
        ''' 
        Output:
            - run_result
            - responce
            - files
        '''
        # init
        self.delete_thread()
        sleep_gap = args['sleep gap']
        max_wait = args['max wait']

        # new thread
        thread = self.client.beta.threads.create(
            messages=[
                {
                "role": "user",
                "content": content,
                "file_ids": file_ids
                }
            ]
        )
        print(thread.id)
        self.thread_id = thread.id
        self.log( ('-' * 5) + f'{self.thread_id}' + ('-' * 10))
        self.log('User: \n' + content)

        # run
        run_result = None
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant.id
            )
        print(run.id)
        for i in range(max_wait//sleep_gap+1):
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print(i * sleep_gap, run.status)
            if not (run.status in ['in_progress', 'queued']):
                print(run.status)
                run_result = run.status # == 'completed'
                break
            if i >= max_wait//sleep_gap:
                run = self.client.beta.threads.runs.cancel(
                    thread_id=thread.id,
                    run_id=run.id
                    )
                run_result = 'time out'
                break
            time.sleep(sleep_gap)

        if run_result != 'completed':
            return run_result, None, None
        
        # get responce
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id
            )
        num_responce = len(messages.data)
        responces = []
        files = []
        for i in range(num_responce-2, -1, -1):
            this_responce = messages.data[i].content[0].text.value 
            responces.append(this_responce)
            for annotation in messages.data[i].content[0].text.annotations:
                if hasattr(annotation, 'file_path'):
                    this_file_id = annotation.file_path.file_id
                    this_file_content = self.client.files.content(this_file_id).read().decode("utf-8")
                    files.append(this_file_content)
        
        self.log('ChatGPT: \n' + '\n'.join(responces))
        if len(files) > 0:
            self.log('\n'.join(files))
        
        return run_result, responces, files


