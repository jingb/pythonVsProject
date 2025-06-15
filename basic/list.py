
squares = [1, 4, 9, 16, 25]
a = squares[-3:]

print(a) #[9, 16, 25]

squares[3]=334

print(a) #[9, 16, 25]

print(squares) #[1, 4, 9, 334, 25]

# [index:]
# 不可变对象（如整数、字符串），浅拷贝和深拷贝没有区别
# 可变对象（如列表、字典），浅拷贝会共享这些对象的引用

print("-------------------------------")

intList: list[int] = [1, 4, 9, 16, 25, 25]

print(intList)

print(intList.count(25))

intList.remove(25)

print(intList)
