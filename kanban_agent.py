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
            model = "qwen-plus",
            api_key = os.environ.get('qwen'),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    
    def __get_keyvalue(self):
        columns = Column.query.filter_by(dashboard_id = self.dashboard_id).all()
        structured_data = []
        for col in columns:
            tasks = Task.query.filter_by(column_id=col.id).order_by(Task.created_at).all()
            current_time = datetime.now()
            task_list = [f"{t.title} - created {(current_time - t.created_at).days} days" for t in tasks]
            
            urgent_tasks = [f" {t.title} --- remind {(t.due_date - current_time).days} days" for t in tasks if t.due_date and (t.due_date - current_time).days <= 3]

            col_summary = {
                "Total tasks": len(tasks),
                "Tasks": "\n".join(task_list),
                "Urgent Tasks": "\n".join(urgent_tasks) if urgent_tasks else "None" 
            }
            
            structured_data.append({
                "key": f"【{col.title}】",
                "value": "\n".join([f"{k}: {v}" for k, v in col_summary.items()])
            })
        
        return structured_data



    def generate_summary(self):
        self.memory.clear()
        kvdata = self.__get_keyvalue()

        for kv in kvdata:
            self.memory.save_context(
                {"input":kv["key"]},
                {"output":kv["value"]},
            )
        prompt_template = """
            You are an excellent summarizing assistant and you can summarize the current task in great detail and well.
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
