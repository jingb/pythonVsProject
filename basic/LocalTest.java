package com.jingb.nonweb;

import com.google.common.collect.Lists;
import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class LocalTest {

    public static void main(String[] args) {
        Course math = new Course("数学");
        Course english = new Course("英语");
        Course chinese = new Course("语文");

        Class clazz1 = new Class("一班");
        Class clazz2 = new Class("二班");

        Student s1 = new Student("s1", 20, clazz1, Lists.newArrayList(math, english));
        Student s2 = new Student("s2", 21, clazz1, Lists.newArrayList(math, english, chinese));

        Student s3 = new Student("s3", 20, clazz2, Lists.newArrayList(math, english, chinese));
        Student s4 = new Student("s4", 19, clazz2, Lists.newArrayList(chinese));
        Student s5 = new Student("s5", 21, clazz2, Lists.newArrayList(english));

        List<Student> stuList = Lists.newArrayList(s1, s2, s3, s4, s5);

        // 把学生按照条件过滤再按班级统计人数
        Map<Class, Long> clazzCountMap = stuList.stream()
                .filter(item -> item.age >= 20) // 把学生根据某些条件先过滤
                .filter(item -> item.age <= 30) // 二次过滤
                .collect(Collectors.groupingBy(Student::getClazz, Collectors.counting()));
        clazzCountMap.forEach((clazz, count) ->
                System.out.println(clazz.getName() + ": " + count));
        System.out.println();

        // 把学生按照条件过滤再按班级统计平均年龄
        Map<Class, Double> clazzAvgtMap = stuList.stream()
                .filter(item -> item.age >= 20) // 把学生根据某些条件先过滤
                .filter(item -> item.age <= 30) // 二次过滤
                .collect(Collectors.groupingBy(Student::getClazz, Collectors.averagingInt(Student::getAge)));
        clazzAvgtMap.forEach((clazz, num) ->
                System.out.println(clazz.getName() + ": " + num));
        System.out.println();

        // 把学生按照条件过滤再分组
        Map<Class, List<Student>> clazzStuListMap = stuList.stream()
                .filter(item -> item.age >= 20) // 把学生根据某些条件先过滤
                .filter(item -> item.age <= 30) // 二次过滤
                .collect(Collectors.groupingBy(Student::getClazz));
        clazzStuListMap.forEach((clazz, lst) ->
                System.out.println(clazz.getName() + ": " + lst.stream().map(Student::getName).collect(Collectors.toList())));
        System.out.println();

        // map<班级, map<年龄段, 学生列表>>
        // 先按班级分组，再按年龄段分组，注意这里年龄段是个自定义的函数
        Map<Class, Map<String, List<Student>>> m = stuList.stream()
            .collect(Collectors.groupingBy(Student::getClazz,
                Collectors.groupingBy(s -> {
                    int age = s.getAge();
                    if (age < 20) return "0-19岁";
                    else if (age < 30) return "20-29岁";
                    else return "30岁+";
                })));
    }
}

@Data
@AllArgsConstructor
class Class {
    String name;
}

@Data
@AllArgsConstructor
class Course {
    String name;
}

@Data
@AllArgsConstructor
class Student {
    String name;
    int age;
    Class clazz;
    List<Course> courseList;
}