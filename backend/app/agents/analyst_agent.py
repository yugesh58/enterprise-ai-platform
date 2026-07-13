import pandas as pd

from app.agents.base_agent import BaseAgent
from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse

from app.services.pandas_generator import generate_pandas_query
from app.services.pandas_executor import execute_pandas_query
from app.services.chart_generator import generate_chart
from app.services.analyst_summarizer import analyst_summarizer


class AnalystAgent(BaseAgent):

    def execute(
        self,
        request: AgentRequest
    ) -> AgentResponse:

        self.logger.info("Executing Analyst Agent")

        df = pd.read_csv(
            "app/uploads/sales.csv"
        )

        columns = list(df.columns)

        pandas_code = generate_pandas_query(
            question=request.question,
            columns=columns,
        )

        result = execute_pandas_query(
            pandas_code=pandas_code,
            df=df,
        )

        chart_path = generate_chart(result)

        summary = analyst_summarizer(
            request.question,
            result,
        )

        request.context.selected_agent = "analyst"

        return AgentResponse(
            answer=summary,
            data={
                "generated_code": pandas_code,
                "chart_path": chart_path,
                "result": str(result),
            },
        )