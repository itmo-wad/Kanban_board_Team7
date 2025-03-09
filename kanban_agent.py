from langchain_openai import OpenAI, ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from app import app, db, User, Dashboard, Column, Task
from datetime import datetime
import os
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
def safe_predict(llm, prompt):
    return llm.predict(prompt)

class KanbanAgent:
    def __init__(self, dashboard_id):
        self.dashboard_id = dashboard_id
        self.llm = self._init_llm()
        self.memory = ConversationSummaryMemory(llm=self.llm)
        
    def _init_llm(self):
        return ChatOpenAI(
            model="qwen-plus",
            api_key= "sk-d55a252e6e0a423895317ec6bb519bbb",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            temperature=0.7
        )
    
    def __get_keyvalue(self):
        columns = Column.query.filter_by(dashboard_id = self.dashboard_id).all()
        structured_data = []
        for col in columns:
            tasks = Task.query.filter_by(column_id=col.id).all()

            col_summary = {
                "Total tasks": len(tasks),
                "Tasks": [t.title for t in tasks[:2]],
                # "Urgent Tasks": sum(1 for t in tasks if self._is_urgent(t)),
            }
            
            structured_data.append({
                "key": f"【{col.title}】",
                "value": "\n".join([f"{v}" for _, v in col_summary.items()])
            })
        
        return structured_data

    # def _is_urgent(self, task):
    #     if task.due_date:
    #         delta = task.due_date - datetime.utcnow()
    #         return 0 < delta.days <= 3
    #     return False


    def generate_summary(self):
        kvdata = self.__get_keyvalue()

        for kv in kvdata:
            self.memory.save_context(
                {"input":kv["key"]},
                {"output":kv["value"]},
            )
        prompt_template = """
            [Base on the kanban data analysis the report]:
            {history}

            [Generate Requirements]:
            1. Task summary (required):
                - List all tasks by column
                - Each task format: Task name - Creation days
            2. Urgent task reminder (optional but needs to be highlighted):
                - Mark as urgent only when the task start time is ≤3 days from the current time
                - Use a unified format: 🚨 Urgent task: [task name] --- Remaining time: [X days]  
            3. Optimization suggestions (required):
                - Make 3 suggestions based on task distribution and urgency
             
            [Prohibited Content]
            - Any information not related to the above three sections
            - Repetitive descriptions
            - Unverified speculations
            """

        prompt = prompt_template.format(
            history = self.memory.buffer
        )

        response = safe_predict(self.llm, prompt)
        return response