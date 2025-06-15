

# 和java go没有区别，因为L被初始化成了List类型

def f(a, L=[]):
    L.append(a)
    return L

print(f(1)) # -> [1]
print(f(2))	# -> [1, 2]
print(f(3)) # -> [1, 2, 3]

print("-----------------------")

arr: list[int] = [1,2,3]
print(f(3, arr))

print("-----------------------------")



def cheeseshop(kind: str, *arguments, **keywords) -> None:
    print("-- Do you have any", kind, "?")
    print("-- I'm sorry, we're all out of", kind)
    for arg in arguments:
        print(arg)
    print("-" * 40)
    for kw in keywords:
        print(kw, ":", keywords[kw])

ret = cheeseshop("Limburger", "It's very runny, sir.",
           "It's really very, VERY runny, sir.",
           shopkeeper="Michael Palin",
           client="John Cleese",
           sketch="Cheese Shop Sketch")

print(ret)

print("jingb")