#!/usr/bin/env python
# encoding: utf-8


def get_item_score(item_list, total_score, reverse=False):
    max_value = max(item_list)

    result = {}
    for item in item_list:

        if reverse:
            '''
                eg. if no container on server No.1 , then container_num load item
                    No.1 server get top score
            '''
            item_score = total_score
            if item != 0:
                #  import pdb
                #  pdb.set_trace()
                item_score = total_score * (max_value - item) / max_value
        else:
            item_score = total_score * item / max_value
        result.setdefault(item, int(item_score))

    return result


if __name__ == '__main__':
    container_num_list = [x for x in range(30)]
    #  container_num_list = [19, 20]
    container_total_score = 15
    container_score = get_item_score(container_num_list, container_total_score, False)
    print container_score
