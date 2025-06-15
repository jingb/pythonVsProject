
s = '''{
    "a": 123123,
    "b": "qwqwq",
    "c": [1,2]
}'''

print(s, "支持多行字符串打印，类似go里面``可以把json包起来")


print('Hello\tWorld')  # \t 会被解释为制表符
print(r'Hello\tWorld') # \t 会原样输出

print("------------------------------------------")

str2 = "jingb,eliza,haha"
res1 = str2.split(",")
print(res1)

res1 = str2.split(",", 1)
print(res1, "最多切几次")

print("------------------------------------------")



