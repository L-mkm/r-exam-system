from models.db import db
from models.user import User
from models.tag import Tag
from models.category import Category
from models.question_tag import question_tag
from models.question import Question
from models.question_option import QuestionOption
from models.exam import Exam
from models.exam_question import ExamQuestion
from models.score import Score
from models.student_answer import StudentAnswer

# 第六次：debug，典型的循环导入问题，在使用SQLAlchemy定义模型关系时很常见