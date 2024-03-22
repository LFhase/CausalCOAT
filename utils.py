import os

class Logger():
    def __init__(self, root, exp_name):
        # Set path
        self.log_root_path = os.path.join(root, f'logs/{exp_name}')
        self.category = ['conversation', 'factors', 'causal_graph']

        # init log files
        if not os.path.exists(self.log_root_path):
            os.makedirs(self.log_root_path)

    def straight_write(self, cate, content, mode='a'):
        assert cate in self.category
        with open(os.path.join(self.log_root_path, cate+'.log'), mode) as file:
            file.write('\n'+content+'\n')

def get_value_from_responce(responce):
    if responce is None:
        return 'None'
    if 'he value is:' not in responce:
        return '?'
    last_part = responce.split('The value is:')[-1]
    if '-1' in last_part:
        return -1
    elif '0' in last_part:
        return 0
    elif '1' in last_part:
        return 1
