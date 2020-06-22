from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from StudentsManager import mforms
from DataModel import models
import hashlib
import datetime

def logout(request):
    try:
        del request.session['user_id']
        del request.session['user_type']
    except KeyError:
        pass
    return redirect('../index')

def course_cross(c1, c2):
    if c1.StartDate.weekday() != c2.StartDate.weekday():
        return False
    if c1.StartClass > c2.EndClass or c1.EndClass < c2.StartClass:
        return False
    if c1.StartDate < c2.StartDate:
        (c1, c2) = (c2, c1)
    timeDelta = c1.StartDate - c2.StartDate
    wks = timeDelta.days // 7
    if c2.Times > wks:
        return True
    else:
        return False

def assign_message(request, context):
    if request.GET:
        mes = request.GET.get('message', False)
        if mes:
            context['Message'] = mes

def get_user_context(request):
    if request.session.get('user_id', False):
        userContext = {}
        if request.session['user_type'] == 'student':
            userContext['Type'] = 'Student'
            user = models.Students.objects.get(pk=request.session['user_id'])
            userContext['Majority'] = {
                'Id': user.Majority.Id,
                'Name': user.Majority.Name,
            }
            userContext['Collage'] = {
                'Id': user.Majority.Collage.Id,
                'Name': user.Majority.Collage.Name,
            }
        else:
            userContext['Type'] = 'Teacher'
            user = models.Teachers.objects.get(pk=request.session['user_id'])
            userContext['Super'] = user.Super
            userContext['Collage'] = {
                'Id': user.Collage.Id,
                'Name': user.Collage.Name,
            }
        userContext['Id'] = user.Id
        userContext['Name'] = user.Name
        userContext['Description'] = user.Description
        return userContext
    else:
        return False

def get_course_context(course):
    endDate = course.StartDate + \
        datetime.timedelta(weeks=(course.Times - 1))
    return {
        'CourseId': course.Id,
        'CourseName': course.Name,
        'TeacherName': course.Teacher.Name,
        'Credit': course.Credit,
        'CourseTime': '星期' + str(course.StartDate.weekday() + 1) +\
            ' 第' + str(course.StartClass) +
            '~' + str(course.EndClass) + '节，' + str(course.StartDate) + \
            '~' + str(endDate),
        'CoursePlace': course.Place,
        'CourseDescription': course.Description,
    }

def get_index(request):
    user_context = get_user_context(request)
    # check if logined
    if user_context:
        context = {'User': user_context}
        if user_context['Type'] == 'Student':
            context['Content'] = render(request, 'index_stu_main.html', context)\
                .content.decode(encoding='utf-8')
        else:
            context['Content'] = render(request, 'index_tea_main.html', context)\
                .content.decode(encoding='utf-8')
        assign_message(request, context)
        return render(request, 'index.html', context)
    # redirect to login
    else:
        return render(request, 'login_pre.html')

def stu_quit_course(request):
    user_context = get_user_context(request)
    if user_context and\
        (user_context['Type'] == 'Student'\
            or user_context['Super']):
        studentId = request.GET.get('student_id')
        courseId = request.GET.get('course_id')
        ress = models.StuCse.objects.filter(Student_id=studentId)\
            .filter(Course_id=courseId)
        for res in ress:
            if not res.Completed:
                res.delete()
            else:
                return redirect(request.GET.get('next') + '退课失败：已录入成绩')
        return redirect(request.GET.get('next') + '退课成功')

def set_user_description(request):
    user_context = get_user_context(request)
    new_des = request.GET.get('description', False)
    if user_context and new_des:
        userId = user_context['Id']
        if user_context['Type'] == 'Student':
            user = models.Students.objects.get(pk=userId)
        else:
            user = models.Teachers.objects.get(pk=userId)
        user.Description = new_des
        user.save()
        return redirect('index')

def stu_select_course(request):
    user_context = get_user_context(request)
    if user_context and\
        (user_context['Type'] == 'Student' or user_context['Super']):
        context = {'User': user_context}
        studentId = request.GET.get('student_id')
        student = models.Students.objects.filter(pk=studentId)
        if student.exists():
            student = student.first()
        else:
            return redirect(request.GET.get('next') +
                '选课失败：学生不存在')
        courseId = request.GET.get('course_id')
        course = models.Courses.objects.get(pk=courseId)
        if not models.MajCse.objects.filter(Majority=student.Majority)\
            .filter(Course=course).exists():
            return redirect(request.GET.get('next') +
                    '选课失败：课程未对相应专业开放')

        selected = models.StuCse.objects.filter(Student_id=studentId).iterator()

        for sel in selected:
            if sel.Course == course:
                return redirect(request.GET.get('next') +
                    '选课失败：课程已选择')
            if course_cross(sel.Course, course):
                return redirect(request.GET.get('next') + \
                    '选课失败：课程与{0} {1}时间冲突'.format(\
                        sel.Course.Id, sel.Course.Name))

        models.StuCse(
            Student=models.Students.objects.get(pk=studentId),
            Course=models.Courses.objects.get(pk=courseId),
            Completed=0,
            Score=0
        ).save()
        return redirect(request.GET.get('next') + '选课成功')

def new_course(request):
    user_context = get_user_context(request)
    if user_context and user_context['Type'] == 'Teacher' and user_context['Super']:
        new_course_id = request.GET.get('id')
        new_course_name = request.GET.get('name')
        credit = int(request.GET.get('credit'))
        if credit <= 0:
            return redirect(request.GET.get('next'))
        year = int(request.GET.get('year'))
        if year <= 1000 or year > 3000:
            return redirect(request.GET.get('next'))
        month = int(request.GET.get('month'))
        if month <= 0 or month > 12:
            return redirect(request.GET.get('next'))
        day = int(request.GET.get('day'))
        if day <= 0 or day > 31:
            return redirect(request.GET.get('next'))
        start_class = int(request.GET.get('start_class'))
        if start_class <= 0 or start_class > 8:
            return redirect(request.GET.get('next'))
        end_class = int(request.GET.get('end_class'))
        if end_class <= 0 or end_class > 8:
            return redirect(request.GET.get('next'))
        times = int(request.GET.get('times'))
        if times <= 0:
            return redirect(request.GET.get('next'))
        place = request.GET.get('place')
        teacher_id = request.GET.get('teacher_id')
        if models.Courses.objects.filter(pk=new_course_id).exists():
            return redirect(request.GET.get('next'))
        res = models.Teachers.objects.filter(pk=teacher_id)
        if not res.exists():
            return redirect(request.GET.get('next'))
        models.Courses(
            Id=new_course_id,
            Name=new_course_name,
            Credit=credit,
            Teacher=res.first(),
            StartDate=datetime.datetime(year, month, day),
            StartClass=start_class,
            EndClass=end_class,
            Times=times,
            Place=place,
            Description=''
        ).save()
        return redirect(request.GET.get('next'))

def delete_course(request):
    user_context = get_user_context(request)
    if user_context and user_context['Type'] == 'Teacher' and user_context['Super']:
        course_id = request.GET.get('id')
        models.Courses.objects.get(pk=course_id).delete()
        return redirect(request.GET.get('next') + \
            '课程删除成功')

def update_course_detail(request):
    user_context = get_user_context(request)
    if user_context and user_context['Type'] == 'Teacher':
        try:
            course_id = request.GET.get('id')
            print(user_context)
            if (not user_context['Super']) and not models.Courses.objects.filter(\
                Teacher_id=user_context['Id']).filter(\
                    pk=course_id).exists():
                return redirect(request.GET.get('next') + '更新失败，无权限')
            course = models.Courses.objects.get(pk=course_id)

            if request.GET.get('credit', '') != '':
                credit = int(request.GET.get('credit'))
                if credit <= 0:
                    raise Exception
                else:
                    course.Credit = credit

            if request.GET.get('year', '') != '':
                year = int(request.GET.get('year'))
                if year <= 1000 or year > 3000:
                    raise Exception
                else:
                    course.StartDate._year = year

            if request.GET.get('month', '') != '':
                month = int(request.GET.get('month'))
                if month <= 0 or month > 12:
                    raise Exception
                else:
                    course.StartDate._month = month

            if request.GET.get('day', '') != '':
                day = int(request.GET.get('day'))
                if day <= 0 or day > 31:
                    raise Exception
                else:
                    course.StartDate._day = day

            if request.GET.get('start_class', '') != '':
                start_class = int(request.GET.get('start_class'))
                if start_class <= 0 or start_class > 8:
                    raise Exception
                else:
                    course.StartClass = start_class

            if request.GET.get('end_class', '') != '':
                end_class = int(request.GET.get('end_class'))
                if end_class <= 0 or end_class > 8:
                    raise Exception
                else:
                    course.EndClass = end_class

            if request.GET.get('times', '') != '':
                times = int(request.GET.get('times'))
                if times <= 0:
                    raise Exception
                else:
                    course.Times = times

            if request.GET.get('description', '') != '':
                description = request.GET.get('description')
                course.Description = description

            if request.GET.get('place', '') != '':
                place = request.GET.get('place')
                course.Place = place

            course.save()

            if request.GET.get('add_majority', '') != '':
                maj_id = request.GET.get('add_majority')
                maj = models.Majorities.objects.filter(pk=maj_id)
                if maj.exists():
                    maj = maj.first()
                else:
                    raise Exception
                ress = models.MajCse.objects.filter(Course_id=course_id)\
                    .filter(Majority_id=maj_id)
                if not ress.exists():
                    models.MajCse(
                        Majority = maj,
                        Course = course,
                    ).save()
                else:
                    raise Exception

            if request.GET.get('remove_majority', '') != '':
                maj_id = request.GET.get('remove_majority')
                maj = models.Majorities.objects.filter(pk=maj_id)
                if maj.exists():
                    maj = maj.first()
                else:
                    raise Exception
                ress = models.MajCse.objects.filter(Course_id=course_id)\
                    .filter(Majority_id=maj_id)
                if ress.exists():
                    for res in ress:
                        res.delete()
                else:
                    raise Exception

            return redirect(request.GET.get('next') + '课程信息更新成功')
        except:
            return redirect(request.GET.get('next') + '更新失败，信息填写有误')

def tea_update_score(request):
    user_context = get_user_context(request)
    if user_context and user_context['Type'] == 'Teacher':
        context = {'User': user_context}
        teacherId = user_context['Id']
        courseId = request.GET.get('course_id')
        studentId = request.GET.get('student_id')
        # get score
        try:
            score = float(request.GET.get('score'))
        except:
            score = -1.0
        print(score)
        if score < 0:
            return redirect(reverse('tea_course_detail') + \
                '?id=' + courseId + '&message=录入失败（输入不合法）')
        # vertify the course belongs to the teacher
        course = models.Courses.objects.get(pk=courseId)
        if course.Teacher.Id == teacherId or\
            user_context['Super']:
            ress = models.StuCse.objects.filter(Student_id=studentId)\
               .filter(Course_id=courseId)
            if ress.exists():
                res = ress.first()
                if not res.Completed:
                    res.Score = score
                    res.Completed = 1
                    res.save()
                    return redirect(request.GET.get('next'))
        return redirect('index')

def get_stu_scheduler(request):
    user_context = get_user_context(request)
    # check if logined
    if user_context and user_context['Type'] == 'Student':
        studentId = user_context['Id']
        context = {'User': user_context}
        course_displays = []
        ress = models.StuCse.objects.filter(Student_id=studentId).iterator()
        today = datetime.date.today()
        for res in ress:
            class_day = res.Course.StartDate.weekday()
            class_day_this_week = datetime.datetime.today() + \
                datetime.timedelta(days=class_day - \
                datetime.datetime.today().weekday())
            deltaw = (class_day_this_week.date() - \
                res.Course.StartDate).days // 7
            if deltaw >= 0 and deltaw < res.Course.Times:
                # today is a class day
                course_context = get_course_context(res.Course)
                course_displays.append({
                    'Left': str((class_day + 1) * 12.5),
                    'Top': str(5 + 19*(res.Course.StartClass // 2)),
                    'Height': str((res.Course.EndClass - res.Course.StartClass) * 100),
                    'Description': course_context['CourseName'] + '，' + \
                        course_context['TeacherName'] + '，' + \
                        course_context['CoursePlace'],
                })
        context['CourseDisplays'] = course_displays
        context['Today'] = str(datetime.datetime.today().date()) + \
            '，星期 ' + str(datetime.datetime.today().weekday() + 1)
        context['Content'] = render(request, 'index_stu_scheduler.html', context)\
            .content.decode(encoding='utf-8')
        assign_message(request, context)
        return render(request, 'index.html', context)
    # redirect to index
    return redirect('../index')

def get_tea_scheduler(request):
    user_context = get_user_context(request)
    # check if logined
    if user_context and user_context['Type'] == 'Teacher':
        teacherId = user_context['Id']
        context = {'User': user_context}
        course_displays = []
        ress = models.Courses.objects.filter(Teacher_id=teacherId).iterator()
        today = datetime.date.today()
        for res in ress:
            class_day = res.StartDate.weekday()
            class_day_this_week = datetime.datetime.today() + \
                datetime.timedelta(days=class_day -
                                   datetime.datetime.today().weekday())
            deltaw = (class_day_this_week.date() -
                      res.StartDate).days // 7
            if deltaw >= 0 and deltaw < res.Times:
                # today is a class day
                course_context = get_course_context(res)
                course_displays.append({
                    'Left': str((class_day + 1) * 12.5),
                    'Top': str(5 + 19*(res.StartClass // 2)),
                    'Height': str((res.EndClass - res.StartClass) * 100),
                    'Description': course_context['CourseName'] + '，' +
                    course_context['CoursePlace'],
                    'Id': course_context['CourseId'],
                })
        context['CourseDisplays'] = course_displays
        context['Today'] = str(datetime.datetime.today().date()) + \
            '，星期 ' + str(datetime.datetime.today().weekday() + 1)
        context['Content'] = render(request, 'index_tea_scheduler.html', context)\
            .content.decode(encoding='utf-8')
        assign_message(request, context)
        return render(request, 'index.html', context)
    # redirect to index
    return redirect('../index')

def get_tea_course_detail(request):
    user_context = get_user_context(request)
    # check if logined
    if user_context and user_context['Type'] == 'Teacher':
        teacherId = user_context['Id']
        context = {'User': user_context}
        courseId = request.GET.get('id', False)
        if courseId:
            course = models.Courses.objects.get(pk=courseId)
            course_context = get_course_context(course)
            context['Course'] = course_context
            ress = models.StuCse.objects.filter(Course_id=courseId)
            students = []
            for res in ress:
                students.append({
                    'Id': res.Student.Id,
                    'Name': res.Student.Name,
                    'CollageName': res.Student.Majority.Collage.Name,
                    'Completed': res.Completed,
                    'Score': res.Score if res.Completed else '未获得分数'
                })
            ress = models.MajCse.objects.filter(Course_id=courseId)
            majorities = []
            for res in ress:
                majorities.append({
                    'Name': res.Majority.Name,
                    'Id': res.Majority.Id
                })
            context['Majorities'] = majorities
            context['Students'] = students
        context['Content'] = render(request,\
            'index_tea_course_detail.html', context)\
            .content.decode(encoding='utf-8')
        assign_message(request, context)
        return render(request, 'index.html', context)
    # redirect to index
    return redirect('../index')

def get_stu_score(request):
    user_context = get_user_context(request)
    # check if logined
    if user_context and user_context['Type'] == 'Student':
        context = {'User': user_context}
        # get courses with scores
        stucses = models.StuCse.objects.filter(Student=context['User']['Id'])
        course_scores = []
        credit_sum = 0
        credit_completed = 0
        average_score = 0
        for stucse in stucses:
            credit_sum += stucse.Course.Credit
            if stucse.Completed:
                credit_completed += stucse.Course.Credit
                average_score += stucse.Score * stucse.Course.Credit
                course_scores.append({
                    'CourseId': stucse.Course.Id,
                    'CourseName': stucse.Course.Name,
                    'TeacherName': stucse.Course.Teacher.Name,
                    'Credit': stucse.Course.Credit,
                    'Score': stucse.Score,
                })
        context['Content'] = render(request, 'index_stu_score.html', {
                'CourseScores': course_scores,
                'Statistics': {
                    'Credits': credit_sum,
                    'CreditsCompleted': credit_completed,
                    'AverageScore':
                        0 if credit_completed == 0 else average_score / credit_completed,
                }
            })\
            .content.decode(encoding='utf-8')
        assign_message(request, context)
        return render(request, 'index.html', context)
    # redirect to index
    return redirect('../index')

def get_stu_course(request):
    user_context = get_user_context(request)
    # check if logined
    if user_context and user_context['Type'] == 'Student':
        context = {'User': user_context}
        # get courses with scores
        stucses = models.StuCse.objects.filter(
            Student=context['User']['Id'])
        courses_completed = []
        courses_uncompleted = []
        courses_unselected = []
        for stucse in stucses:
            course_context = get_course_context(stucse.Course)
            if stucse.Completed:
                courses_completed.append(course_context)
            else:
                courses_uncompleted.append(course_context)
        cses_iter = models.Courses.objects\
            .exclude(pk__in=stucses.values('Course_id')).iterator()
        for course in cses_iter:
            res = models.MajCse.objects.filter(Course_id=course.Id,\
                Majority_id=context['User']['Majority']['Id'])
            if res.exists():
                courses_unselected.append(
                    get_course_context(course))
        context['Content'] = render(request, 'index_stu_course.html',
            {
                'CoursesCompleted': courses_completed,
                'CoursesUncompleted': courses_uncompleted,
                'CoursesUnselected': courses_unselected,
                'User': user_context
            })\
            .content.decode(encoding='utf-8')
        assign_message(request, context)
        return render(request, 'index.html', context)
    # redirect to index
    return redirect('../index')

def get_tea_course(request):
    user_context = get_user_context(request)
    # check if logined
    if user_context and user_context['Type'] == 'Teacher':
        context = {'User': user_context}
        # get courses with scores
        ress = models.Courses.objects.filter(
            Teacher_id = context['User']['Id'])
        courses = []
        global_courses = []
        for res in ress:
            course_context = get_course_context(res)
            courses.append(course_context)
        if user_context['Super']:
            for res in models.Courses.objects.all().iterator():
                course_context = get_course_context(res)
                global_courses.append(course_context)
        context['Content'] = render(request, 'index_tea_course.html',
            {'Courses': courses, 'User': user_context, 'GlobalCourses': global_courses})\
            .content.decode(encoding='utf-8')
        assign_message(request, context)
        return render(request, 'index.html', context)
    # redirect to index
    return redirect('../index')

def get_jw_students(request):
    user_context = get_user_context(request)  # check if logined
    if user_context and user_context['Type'] == 'Teacher'\
        and user_context['Super']:
        context = { 'User': user_context }

        category = []
        colls = models.Collages.objects.all().iterator()
        for coll in colls:
            majs_mes = []
            majs = models.Majorities.objects.filter(Collage=coll)
            for maj in majs:
                majs_mes.append({
                    'Id': maj.Id,
                    'Name': maj.Name,
                })
            category.append({
                'Id': coll.Id,
                'Name': coll.Name,
                'Majorities': majs_mes
            })
        context['Category'] = category

        if request.GET.get('id', '') != '':
            maj_id = request.GET.get('id')
            maj = models.Majorities.objects.get(pk=maj_id)
            stus = models.Students.objects.filter(Majority_id=maj_id)
            students = []
            for stu in stus:
                cds = 0
                scs = 0
                ress = models.StuCse.objects.filter(Student=stu)
                for res in ress:
                    if res.Completed:
                        cds += res.Course.Credit
                        scs += res.Score * res.Course.Credit
                if cds != 0:
                    scs /= cds
                students.append({
                    'Id': stu.Id,
                    'Name': stu.Name,
                    'Credit': cds,
                    'Score': scs
                })
            context['Students'] = students
            context['Majority'] = {
                'Id': maj.Id,
                'Name': maj.Name,
                'Collage': {
                    'Id': maj.Collage.Id,
                    'Name': maj.Collage.Name
                }
            }
        context['Content'] = render(request, 'index_jw_students.html', context)\
            .content.decode(encoding='utf-8')
        assign_message(request, context)
        return render(request, 'index.html', context)
    return redirect('../index')

def new_user(request):
    user_context = get_user_context(request)  # check if logined
    if user_context and user_context['Type'] == 'Teacher'\
            and user_context['Super']:
        context = {'User': user_context}
        if request.GET.get('type', '') == 'student':
            stu_id = request.GET.get('id')
            stu_name = request.GET.get('name')
            stu_majority_id = request.GET.get('maj_id')
            majority = models.Majorities.objects.get(pk=stu_majority_id)
            if not models.Students.objects.filter(pk=stu_id).exists():
                models.Students(
                    Id = stu_id,
                    Name = stu_name,
                    Majority = majority,
                    Description = '',
                    PasswordMd5 = hashlib.md5(stu_id.encode(encoding='utf-8')).hexdigest()
                ).save()
                return redirect(request.GET.get('next') + '录入成功')
    return redirect('index')

def get_login_as_student(request):
    context = {'UserNameLabel': '学号', 'StuOrTea': '学生',
               'PostAddress': '../login_student/'}
    # login
    if request.POST:
        form = mforms.LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # verify is id exists
            record = models.Students.objects.filter(pk=data['id'])
            if record.exists():
                # verify is password correct
                passMd5 = str(record.first().PasswordMd5)
                inputMd5 = hashlib.md5(data['password'].encode(encoding='utf-8')).hexdigest()
                if passMd5 == inputMd5:
                    request.session['user_id'] = record.first().Id
                    request.session['user_type'] = 'student'
                    return redirect('../index')
                else:
                    context['ErrorMessage'] = '登陆失败，密码错误'
            else:
                context['ErrorMessage'] = '登陆失败，学号不存在'
        else:
            context['ErrorMessage'] = '请将信息填写完整'
        return render(request, 'login.html', context)
    # get login page
    else:
        if request.session.get('user_id', False):
            if request.session['user_type'] == 'student':
                stu = models.Students.objects.get(
                    pk=request.session['user_id'])
                return redirect('../index')

                # have logined
        return render(request, 'login.html', context)

def get_login_as_teacher(request):
    context = {'UserNameLabel': '教工号', 'StuOrTea': '教师',
               'PostAddress': '../login_teacher/'}
    # login
    if request.POST:
        form = mforms.LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # verify is id exists
            record = models.Teachers.objects.filter(pk=data['id'])
            if record.exists():
                # verify is password correct
                passMd5 = str(record.first().PasswordMd5)
                inputMd5 = hashlib.md5(data['password'].encode(
                    encoding='utf-8')).hexdigest()
                if passMd5 == inputMd5:
                    request.session['user_id'] = record.first().Id
                    request.session['user_type'] = 'teacher'
                    return redirect('../index')
                else:
                    context['ErrorMessage'] = '登陆失败，密码错误'
            else:
                context['ErrorMessage'] = '登陆失败，教工号不存在'
        else:
            context['ErrorMessage'] = '请将信息填写完整'
        return render(request, 'login.html', context)
    # get login page
    else:
        if request.session.get('user_id', False):
            if request.session['user_type'] == 'teacher':
                stu = models.Teachers.objects.get(
                    pk=request.session['user_id'])
                return redirect('../index')
                # have logined
        return render(request, 'login.html', context)
