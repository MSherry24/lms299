# TODO
#  Fix mapping tables to use joins.
#  
# ROLES = ('teacher','student','auditor','grader')

STUDENT, TEACHER = 'student','teacher'

NE = IS_NOT_EMPTY()

db.define_table(
    'course',
    Field('name',requires=NE),
    Field('code',requires=NE),
    Field('prerequisites','list:string'),  # This should be a reference to another course.
    Field('description','text'),
    Field('tags','list:string'),
    format='%(code)s: %(name)s')

db.define_table(
    'course_section',
    Field('name',requires=NE),
    Field('course','reference course'),
    Field('meeting_time','string'),
    Field('meeting_place','string'),
    Field('signup_deadline','date'),
    Field('drop_deadline','date'),
    Field('start_date','date'),
    Field('stop_date','date'),
    Field('syllabus','text'),
    Field('private_info','text'),
    Field('on_line','boolean',default=False,label='Online'),
    Field('inclass','boolean',default=True),
    format='%(name)s')


db.define_table(
    'membership',
    Field('course_section','reference course_section'),
    Field('auth_user','reference auth_user'),
    Field('role', requires=IS_IN_SET((STUDENT, TEACHER))),
    auth.signature)

db.define_table(
    'doc',
    Field('name',requires=NE),
    Field('course_section','reference course_section',writable=False,readable=False),
    Field('filename','upload',label='Content'),   
    auth.signature)

db.define_table(
    'homework',
    Field('name',requires=NE),
    Field('course_section','reference course_section'),
    Field('description','text'),
    Field('due_date','datetime'),
    Field('filename','upload'))

db.define_table(
    'occurrance',
    Field('name',requires=NE),
    Field('description','text'),
    Field('posted_datetime','datetime',default=request.now),
    Field('start_datetime','datetime',default=request.now),
    Field('stop_datetime','datetime',default=request.now),
    Field('course_section','reference course_section',
          requires=IS_EMPTY_OR(IS_IN_DB(db,'course_section.id','%(name)s'))),
    auth.signature)


def my_sections(user_id=auth.user_id, course_id=None, roles=[TEACHER, STUDENT],max_sections=20):
    """
    returns a Rows of Sections the user_id is in in any of the speficied roles (teacher or student)
    if a course_id is specified it returns only sections for that course id (default to all courses)
    if max_sections is specified limits the search results (defaults to 20)
    """
    query = ((db.membership.course_section==db.course_section.id)&
             (db.membership.auth_user==user_id)&
             (db.membership.role.belongs(roles)))
    if course_id:
        query &= db.course_section.course==course_id
    return db(query).select(db.course_section.ALL,limitby=(0,max_sections))

def is_user_student(section_id, user_id=auth.user_id):
    """
    checks if the user_id (or the current user) is enrolled in the section_id as a student
    """
    return db((db.membership.course_section==section_id) &
              (db.membership.role==STUDENT) &
              (db.membership.auth_user==user_id)).count() > 0

def is_user_teacher(section_id, user_id=auth.user_id):
    """
    checks if the user_id (or the current user) is the teacher of a the section_id
    """
    return db((db.membership.course_section==section_id) &
              (db.membership.role==TEACHER) &
              (db.membership.auth_user==user_id)).count() > 0

def users_in_section(section_id,roles=[STUDENT]):
    """
    returns a list of users with a role (default STUDENT role) in the section_id    
    """
    return db((db.membership.course_section == section_id) &
              (db.membership.role.belongs(roles))&
              (db.membership.auth_user == db.auth_user.id)).select(db.auth_user.ALL)

####################################################################################################
# Populate some tables so we have data with which to work.
if db(db.auth_user).isempty():
    import datetime
    from gluon.contrib.populate import populate
    mdp_id = db.auth_user.insert(first_name="Good",last_name='Teacher',
                                 email='good.teacher@example.com',
                                 password=CRYPT()('test')[0])

    populate(db.auth_user,300)
    db(db.auth_user.id>1).update(is_student=True,is_teacher=False,is_administrator=False)


    # Add everyone in the auth_user table - except Massimo - to the student group.
    for k in range(200,300):
        id = db.course.insert(name="Dummy course",
                              code="CSC%s" % k,
                              prerequisites=[],
                              tags=[],
                              description = 'description...')
        for s in range(701,703):
            i = db.course_section.insert(
                name="CSC%s-%s" % (k,s),
                course=id,
                meeting_place="CDM",
                meeting_time="Tuesday",
                start_date=datetime.date(2014,9,1),
                stop_date=datetime.date(2014,12,1),
                signup_deadline=datetime.date(2014,11,10))
            rows = db(db.auth_user).select(limitby=(0,10),orderby='<random>')
            db.membership.insert(course_section=i, auth_user=mdp_id, role='teacher')
            for row in rows:
                db.membership.insert(course_section=i, auth_user=row.id, role='teacher')

# add logic to add me and massimo to the admin and teacter groups
# students = db((db.auth_user.first_name != 'Massimo') | (db.auth_user.first_name != 'Bryan')).select(db.auth_user.id)
# for student in students:
#     db.auth_membership.insert(user_id=student.id, group_id=2)
####################################################################################################
