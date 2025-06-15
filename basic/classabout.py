
class Course:
    def __init__(self, name: str):
        self.name: str = name 

class Class:
    # 班级
    def __init__(self, name: str):
        self.name: str = name 

class Student:
    def __init__(self, name :str, age :int, clazz :Class):
        self.name = name 
        self.age = age 
        self.clazz = clazz
        self.courseList :list[Course] = []

    def __repr__(self):
        return f"Student(name={self.name}, age={self.age}, clazz={self.clazz.name})"

math = Course("数学")
english = Course("英语")
chinese = Course("语文")

clazz1 = Class("一班")
clazz2 = Class("二班")

s1 = Student("s1", 20, clazz1)
s2 = Student("s2", 21, clazz1)

s3 = Student("s3", 20, clazz2)
s4 = Student("s4", 19, clazz2)
s5 = Student("s5", 21, clazz2)
s6 = Student("s6", 19, clazz2)

stuList :list[Student] = [s1, s2, s3, s4, s5, s6]

# original_dict = {'a': 1, 'b': 2, 'c': 3}
# swapped = {v: k for k, v in original_dict.items()}

# 把学生按照条件过滤再按班级统计人数
# 这里面两层嵌套
filtered_count = {
    clazz.name: len([s 
                     for s in stuList 
                        if s.clazz == clazz and s.age >= 19])
    for clazz in {s.clazz for s in stuList}
}
print("filtered_count", filtered_count)

# 把学生按照条件过滤再按班级分组
groupByClazz = {
    clazz.name: [s for s in stuList 
                    if s.clazz == clazz and s.age >= 20]
    for clazz in {s.clazz for s in stuList}
}
print("根据条件按照班级分组", groupByClazz)
assert len(groupByClazz["一班"]) == 2
assert len(groupByClazz["二班"]) == 2

print("-------------------------")

# map<班级, map<年龄段, 学生列表>>
# 先按班级分组，再按年龄段分组，注意这里年龄段是个自定义的函数
# groupByAgeRange = {
#     s1.age: [s1 for s in stuList if s.age == s1.age]
#     for s1 in stuList
# }
groupByAgeRange = {}
for student in stuList:
    groupByAgeRange.setdefault(student.age, []).append(student)

print("groupByAgeRange", groupByAgeRange)

assert len(groupByAgeRange[19]) == 2
assert len(groupByAgeRange[20]) == 2
assert len(groupByAgeRange[21]) == 2

# groupByAgeRange = {
#     s1.age: (s1 for s in stuList)
#     for s1 in stuList
# }



# groupByClazzGroupByAgeRange = {
#     clazz.name: {}
#     for clazz in {s.clazz for s in stuList}
# }
# print(groupByClazzGroupByAgeRange)

