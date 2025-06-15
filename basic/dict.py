original_dict = {'a': 1, 'b': 2, 'c': 3}
swapped = {v: k 
           for k, v in original_dict.items()}
print(swapped)  # 输出: {1: 'a', 2: 'b', 3: 'c'}

