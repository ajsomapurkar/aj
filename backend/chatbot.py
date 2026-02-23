# chatbot.py
import json
import knowledge_base as knowledge_base_


class AmbitChatbot:
    def __init__(self):
        self.knowledge_base = knowledge_base_.COLLEGE_DATA

    def get_response(self, query):
        query = query.lower()
        if 'admission' in query:
            return self._format_admissions()
        elif 'fee' in query:
            return self._format_fees()
        elif 'exam' in query or 'vtu' in query:
            return self._format_exams()
        elif 'contact' in query or 'phone' in query or 'email' in query:
            return self._format_contacts()
        elif 'library' in query:
            return self.knowledge_base['facilities']['library']['timing']
        elif 'hostel' in query:
            return "Yes, hostel available. Contact: " + self.knowledge_base['facilities']['hostel']['contact']
        else:
            return self._general_help()

    def _format_admissions(self):
        data = self.knowledge_base['admissions']['undergraduate']
        return f"""Admissions:
- Courses: {', '.join(data['courses'])}
- Eligibility: {data['eligibility']}
- Process: {data['process']}
- Documents: {', '.join(data['documents'])}
- Fees: B.Tech {data['fees']['btech']}, BBA {data['fees']['bba']}, BCA {data['fees']['bca']}"""

    def _format_fees(self):
        fees = self.knowledge_base['admissions']['undergraduate']['fees']
        return f"B.Tech: {fees['btech']}, BBA: {fees['bba']}, BCA: {fees['bca']} (per year)"

    def _format_exams(self):
        exams = self.knowledge_base['examinations']
        return f"""VTU Exams: Odd sem {exams['vtu_schedule']['odd_sem']}, Even sem {exams['vtu_schedule']['even_sem']}
Internal tests: {exams['internal_assessment']['tests']}
Attendance required: {exams['internal_assessment']['attendance']}
Results: {exams['results']['check']}"""

    def _format_contacts(self):
        info = self.knowledge_base['college_info']
        return f"Phone: {info['phone']}, Email: {info['email']}, Address: {info['address']}"

    def _general_help(self):
        return "I can help with admissions, fees, exams, contacts, library, hostel. Please ask specifically."
