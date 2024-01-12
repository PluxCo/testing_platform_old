from data_accessors.questions_accessor import Question
from data_accessors.auth_accessor import GroupsDAO


class BridgeService:
    @staticmethod
    def load_groups_into_questions(questions: list[Question]):
        different_groups = {g_id for q in questions for g_id in q.group_ids}

        if len(different_groups) > 2:
            groups = {g.id: g.label for g in GroupsDAO.get_all_groups()}
        else:
            groups = {}
            for g_id in different_groups:
                g = GroupsDAO.get_group(g_id)
                groups[g.id] = g.label

        for q in questions:
            q.groups = [groups[g_id] for g_id in q.group_ids]
