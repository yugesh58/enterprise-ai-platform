
import streamlit as st
import requests
import pandas as pd


# ============================================
# CHART HELPER
# ============================================

def should_show_chart(df):

    if len(df.columns) != 2:
        return False

    numeric_columns = df.select_dtypes(
        include=["number", "float", "int"]
    ).columns

    return len(numeric_columns) == 1


# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="SQL AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:

    st.header("Project Details")

    st.write("""
    AI SQL Assistant

    Features:
    - LangGraph Workflow
    - Conversational Memory
    - Dynamic Schema Retrieval
    - SQL Validation
    - Self-Correction
    - Result Summarization
    - SQLite Database
    - Streamlit Chat UI
    - Automatic Charts
    """)

    if st.button("Clear Chat"):

        st.session_state.messages = []

        st.rerun()

# ============================================
# TITLE
# ============================================

st.title("🤖 SQL AI Assistant")

# ============================================
# SESSION STATE
# ============================================

if "messages" not in st.session_state:
    st.session_state.messages = []

# ============================================
# DISPLAY CHAT HISTORY
# ============================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "user":

            st.markdown(message["content"])

        else:

            if message.get("summary"):

                st.markdown("### Summary")

                st.info(
                    message["summary"]
                )

            if message.get("sql"):

                st.markdown("### Generated SQL")

                st.code(
                    message["sql"],
                    language="sql"
                )

            if message.get("data"):

                result = message["data"]

                if isinstance(result, list) and len(result) > 0:

                    st.markdown("### Results")

                    df = pd.DataFrame(result)

                    st.dataframe(
                        df,
                        use_container_width=True
                    )

                    if should_show_chart(df):

                        st.markdown("### Chart")

                        x_col = df.columns[0]

                        chart_df = df.set_index(x_col)

                        st.bar_chart(chart_df)

                else:

                    st.warning(
                        "No results found"
                    )

            if message.get("workflow"):

                workflow = message["workflow"]

                with st.expander("Agent Workflow"):

                    st.write("Question")

                    st.code(
                        workflow["question"]
                    )

                    st.write("Generated SQL")

                    st.code(
                        workflow["sql"],
                        language="sql"
                    )

                    st.write("Rows Returned")

                    st.write(
                        workflow["rows"]
                    )

                    st.write("Summary")

                    st.write(
                        workflow["summary"]
                    )

# ============================================
# CHAT INPUT
# ============================================

question = st.chat_input(
    "Ask a database question..."
)

# ============================================
# PROCESS USER INPUT
# ============================================

if question:

    with st.chat_message("user"):

        st.markdown(question)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    try:

        with st.spinner("Thinking..."):

            response = requests.get(
                "https://sql-ai-platform.onrender.com/ask",
                params={
                    "question": question
                }
            )

            data = response.json()

        sql_query = data.get(
            "sql_query",
            ""
        )

        summary = data.get(
            "summary",
            ""
        )

        result = data.get(
            "result",
            []
        )

        with st.chat_message("assistant"):

            if summary:

                st.markdown("### Summary")

                st.info(summary)

            st.markdown("### Generated SQL")

            st.code(
                sql_query,
                language="sql"
            )

            st.markdown("### Results")

            if isinstance(result, list) and len(result) > 0:

                df = pd.DataFrame(result)

                st.dataframe(
                    df,
                    use_container_width=True
                )

                if should_show_chart(df):

                    st.markdown("### Chart")

                    x_col = df.columns[0]

                    chart_df = df.set_index(x_col)

                    st.bar_chart(chart_df)

            else:

                st.warning(
                    "No results found"
                )

            with st.expander("Agent Workflow"):

                st.write("Question")

                st.code(question)

                st.write("Generated SQL")

                st.code(
                    sql_query,
                    language="sql"
                )

                st.write("Rows Returned")

                st.write(
                    len(result)
                )

                st.write("Summary")

                st.write(summary)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "summary": summary,
                "sql": sql_query,
                "data": result,
                "workflow": {
                    "question": question,
                    "sql": sql_query,
                    "rows": len(result),
                    "summary": summary
                }
            }
        )

    except Exception as e:

        with st.chat_message("assistant"):

            st.error(
                f"""
Unable to process request.

Error:
{str(e)}
"""
            )

