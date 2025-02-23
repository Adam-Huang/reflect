import pyperclip
import streamlit as st

# 显示历史消息，按问答对分组
def show_conversation_history():
    for i in range(0, len(st.session_state.session.conversation), 2):
        if i + 1 >= len(st.session_state.session.conversation):
            break

        user_msg = st.session_state.session.conversation[i]
        assistant_msg = st.session_state.session.conversation[i + 1]

        if i not in st.session_state.quotes:
            st.session_state.quotes[i] = False

        # 显示问答对
        with st.container():
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                with st.chat_message(user_msg["role"]):
                    st.markdown(user_msg["content"])
                with st.chat_message(assistant_msg["role"]):
                    with st.expander(assistant_msg["content"][:80]):
                        st.markdown(assistant_msg["content"])
            with col2:
                if st.checkbox("Quote", key=f"quote_{i}", value=st.session_state.quotes[i],
                               on_change=lambda i=i: st.session_state.quotes.update(
                                   {i: not st.session_state.quotes[i]})):
                    # 检查是否已经引用过
                    if user_msg["id"] not in st.session_state.quoted_ids:
                        # 拼接被引用的对话历史
                        st.session_state.quoted_history.extend([user_msg, assistant_msg])
                        st.session_state.quoted_ids.add(user_msg["id"])
                # Copy buttons
                if st.button("Copy User Message", key=f"copy_user_{i}"):
                    pyperclip.copy(user_msg["content"])  # Copy to clipboard
                    st.success("User message copied to clipboard!")

                if st.button("Copy Assistant Message", key=f"copy_assistant_{i}"):
                    pyperclip.copy(assistant_msg["content"])  # Copy to clipboard
                    st.success("Assistant message copied to clipboard!")


def clear_quotes():
    # TODO ask streamlit to fix this
    # for key in st.session_state.keys():
    #     if key.startswith("quote_"):
    #         st.session_state[key] = False
    # 只修改中间变量，不触碰 Widget 的 key
    for i in st.session_state.quotes:
        st.session_state.quotes[i] = False

    st.session_state.quoted_history = []
    st.session_state.quoted_ids = set()
    st.rerun()
