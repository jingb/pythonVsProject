

from datetime import datetime
import time

i = 5

def f(arg=i):
    print(arg, "打印5  这里函数f在声明的时候参数arg已经被初始化了，而不是等函数f被调用时才被初始化")

i = 6
f()  

print("------------------------------")


# def show_time(time=datetime.now()):    # 时间在函数定义时就固定了
#     print(time)

# 正确的做法
def show_time(time=None):
    if time is None:
        time = datetime.now()
    print(time)

# 每次调用都会显示相同的时间
show_time()
time.sleep(1)
show_time()    # 还是显示相同的时间


print("------------------------------")


print("local 和 global两个关键字初步感觉是没有必要的，会很混乱，同样应该从函数设计上来解决")

def scope_test():
    def do_local():
        # 作用域纯在这个函数里面
        spam = "local spam"

    def do_nonlocal():
        nonlocal spam
        spam = "nonlocal spam"

    def notUseNonlocal(s :str) -> str:
        s = "用函数返回值去接结果，而不是nonlocal这样的关键字"
        return s

    def do_global():
        global spam
        spam = "global spam"

    spam = "test spam"
    do_local()
    print("After local assignment:", spam)
    do_nonlocal()
    print("After nonlocal assignment:", spam)
    do_global()
    print("After global assignment:", spam)
    x = notUseNonlocal(spam)
    print("用函数返回值去接结果，而不是nonlocal这样的关键字", x)

scope_test()
print("In global scope:", spam)

