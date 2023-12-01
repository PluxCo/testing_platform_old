from data_accessors.questions_accessor import QuestionsDAO

QuestionsDAO.set_host("http://localhost:3000")
print(list(QuestionsDAO.get_all_questions()))
