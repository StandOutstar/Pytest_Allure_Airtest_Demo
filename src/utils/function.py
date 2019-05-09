from random import randint


def generate_random_num_str(length=20):
    """
    生成随机字母与数字混合字符串
    :param length:
    :return:
    """
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
               'v', 'w', 'x', 'y', 'z']
    random_list = []
    for _ in range(length):
        random_list.append(randint(0, len(letters)) - 1)

    for i, v in enumerate(random_list):
        if i % 2 == 0:
            v %= 10
            random_list[i] = str(v)
            continue
        random_list[i] = letters[v]
    return ''.join(random_list)