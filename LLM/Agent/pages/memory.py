from core.memory import MemoryManager
# Streamlit UI
import streamlit as st

# 设置页面为宽页模式
st.set_page_config(layout="wide")

@st.dialog("Add your Memory")
def add_memory_dialog():
    memory_text = st.text_area("Memory Text", key="memory_text")
    memory_summary = st.text_area("Summary", key="memory_summary")
    memory_labels = st.multiselect("Select Labels", st.session_state.memory_manager.labels, key="memory_labels")
    memory_trigger = st.selectbox("Trigger", ["请选择"] + list(st.session_state.memory_manager.triggers), index=0, key="memory_trigger")
    submit_button = st.button(label='Submit Memory', key="submit_memory")
    if submit_button:
        st.session_state.memory_manager.add_memory(
            memory_text=memory_text,
            summary=memory_summary,
            labels=memory_labels,
            trigger=None if memory_trigger == "请选择" else memory_trigger
        )
        st.success("Memory added successfully!")
        st.rerun()
 
 
@st.dialog("Add your Label")
def add_label_dialog():
    memory_label = st.text_input("Label", key="memory_label")
    label_description = st.text_input("Description", key="label_description")
    submit_button = st.button(label='Submit Label', key="submit_label")
    if submit_button:
        st.session_state.memory_manager.add_label(
            label=memory_label,
            description=label_description
        )
        st.success("Label added successfully!")
 
 
@st.dialog("Add your Trigger")
def add_trigger_dialog():
    memory_trigger = st.text_input("Trigger", key="memory_trigger")
    trigger_description = st.text_input("Description", key="trigger_description")
    submit_button = st.button(label='Submit Label', key="submit_trigger")
    if submit_button:
        st.session_state.memory_manager.add_trigger(
            trigger=memory_trigger,
            description=trigger_description
        )
        st.success("Trigger added successfully!")


@st.dialog("Update Label")
def update_label_dialog():
    labels = list(st.session_state.memory_manager.labels)
    if not labels:
        st.warning("No labels available to update")
        return
        
    old_label = st.selectbox("选择要修改的标签", labels, key="old_label")
    new_label = st.text_input("新标签名称", key="new_label")
    new_description = st.text_input("新描述", key="new_description")
    submit_button = st.button(label='确认修改', key="update_label")
    
    if submit_button:
        if not new_label:
            st.error("新标签名称不能为空")
            return
            
        try:
            st.session_state.memory_manager.update_label(
                old_label=old_label,
                new_label=new_label,
                new_description=new_description
            )
            st.success("Label updated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"更新标签失败: {str(e)}")

@st.dialog("Delete Label")
def delete_label_dialog():
    label = st.selectbox("选择要删除的标签", list(st.session_state.memory_manager.labels), key="delete_label")
    submit_button = st.button(label='确认删除', key="confirm_delete_label")
    if submit_button and label:
        st.session_state.memory_manager.delete_label(label)
        st.success("Label deleted successfully!")
        st.rerun()

@st.dialog("Update Trigger")
def update_trigger_dialog():
    old_trigger = st.selectbox("选择要修改的触发词", list(st.session_state.memory_manager.triggers), key="old_trigger")
    new_trigger = st.text_input("新触发词", key="new_trigger")
    new_description = st.text_input("新描述", key="new_description_trigger")
    submit_button = st.button(label='确认修改', key="update_trigger")
    if submit_button and old_trigger and new_trigger:
        st.session_state.memory_manager.update_trigger(
            old_trigger=old_trigger,
            new_trigger=new_trigger,
            new_description=new_description
        )
        st.success("Trigger updated successfully!")
        st.rerun()

@st.dialog("Delete Trigger")
def delete_trigger_dialog():
    trigger = st.selectbox("选择要删除的触发词", list(st.session_state.memory_manager.triggers), key="delete_trigger")
    submit_button = st.button(label='确认删除', key="confirm_delete_trigger")
    if submit_button and trigger:
        st.session_state.memory_manager.delete_trigger(trigger)
        st.success("Trigger deleted successfully!")
        st.rerun()

@st.dialog("Show your Memory")
def show_memory_dialog():
    memory_manager = st.session_state.memory_manager
 
    search_type = st.selectbox("选择查询类型", ["vector", "keyword", "label", "trigger"], key="search_type")
 
    if search_type == "vector":
        query = st.text_input("输入查询文本", key="vector_query")
        k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5, key="vector_k")
        if st.button("查询", key="vector_search"):
            memories = memory_manager.search_memory(query, k=k, search_type=search_type)
            display_memories(memories, memory_manager)
    elif search_type == "keyword":
        query = st.text_input("输入关键词", key="keyword_query")
        exact_match = st.checkbox("精确匹配", key="exact_match")
        k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5, key="keyword_k")
        if st.button("查询", key="keyword_search"):
            memories = memory_manager.search_memory(query, k=k, search_type=search_type, exact_match=exact_match)
            display_memories(memories, memory_manager)
    elif search_type == "label":
        labels = st.multiselect("选择标签", list(memory_manager.labels), default=[], key="label_select")
        k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5, key="label_k")
        if st.button("查询", key="label_search"):
            memories = memory_manager.search_memory("", labels=labels, k=k, search_type=search_type)
            display_memories(memories, memory_manager)
            return memories
    elif search_type == "trigger":
        query = st.selectbox("选择触发词", list(memory_manager.triggers), key="trigger_select")
        k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5, key="trigger_k")
        if st.button("查询", key="trigger_search"):
            memories = memory_manager.search_memory(query, k=k, search_type=search_type)
            display_memories(memories, memory_manager)
            return memories
    else:
        st.write("无效的查询类型")
 
 
def display_memories(memories, memory_manager):
    if not memories:
        st.write("没有找到匹配的记忆")
        return
 
    for mem in memories:
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            with st.container():
                col4, col5, col6, col7 = st.columns([1, 3, 3, 1])
                with col4:
                    st.write("ID")
                    st.write(mem.id)
                with col5:
                    st.write("创建时间")
                    st.write(mem.created_at)
                with col6:
                    st.write("更新时间")
                    st.write(mem.updated_at)
                with col7:
                    st.write("trigger")
                    st.write(mem.trigger)
 
            st.markdown(mem.summary)
            with st.expander("显示原文"):
                st.markdown(mem.original_text)
        with col2:
            st.write("标签")
            for label in mem.labels:
                st.write(f"`{label}`")
        with col3:
            st.write("操作")
            if st.button(f"删除记忆{mem.id}", key=f"delete_memory_{mem.id}"):
                memory_manager.delete_memory(mem.id)
                st.write(f"记忆 {mem.id} 已删除")
                st.rerun()
            if st.button(f"更新记忆{mem.id}", key=f"update_memory_{mem.id}"):
                update_memory_dialog(mem.id, memory_manager)
 
        # 自定义分割线样式
        st.markdown("""
            <style>
            .custom-hr {
                border: none;
                height: 1px;
                background-color: #ccc;
            }
            </style>
            <hr class="custom-hr">
            """, unsafe_allow_html=True)
 
 
@st.dialog("update your Memory")
def update_memory_dialog(memory_id, memory_manager):
    mem = None
    for m in memory_manager.memory_data:
        if m.id == memory_id:
            mem = m
            break
    if mem is None:
        st.write(f"记忆 {memory_id} 不存在")
        return
 
    st.write(f"当前记忆 ID: {mem.id}")
    st.write(f"当前原文: {mem.original_text}")
    st.write(f"当前摘要: {mem.summary}")
    st.write(f"当前标签: {mem.labels}")
    st.write(f"当前触发词: {mem.trigger}")
 
    labels = st.session_state.memory_manager.labels
    triggers = ["请选择"] + list(st.session_state.memory_manager.triggers)
    new_text = st.text_area("新的原文", value=mem.original_text, key="new_text")
    new_summary = st.text_area("新的摘要", value=mem.summary, key="new_summary")
    new_labels = st.multiselect("新的标签", options=labels, default=mem.labels, key="new_labels")
    default_index = triggers.index(mem.trigger) if mem.trigger in triggers else 0
    new_trigger = st.selectbox("新的触发词", options=triggers, index=default_index, key="new_trigger")
 
    if st.button("更新记忆", key="update_memory"):
        # new_labels_list = [label.strip() for label in new_labels.split(",") if label.strip()]
        memory_manager.update_memory(mem.id, new_text, new_summary, new_labels,
                                     new_trigger=None if new_trigger == "请选择" else new_trigger)
        st.write(f"记忆 {mem.id} 已更新")
        st.rerun()
 
 
def display_buttons(memory_manager):
    st.sidebar.title("Memory Option")
    # """操作按钮"""
    with st.sidebar:
        search_type = st.selectbox("选择查询类型", ["label", "trigger", "keyword", "vector"], key="search_type")
        search_query = ""
        k = 1
        labels = []
        exact_match = None
        if search_type == "vector":
            search_query = st.text_input("输入查询文本", key="vector_query")
            k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5, key="vector_k")
 
        elif search_type == "keyword":
            search_query = st.text_input("输入关键词", key="keyword_query")
            exact_match = st.checkbox("精确匹配", key="exact_match")
            k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5, key="keyword_k")
 
        elif search_type == "label":
            labels = st.multiselect("选择标签", list(memory_manager.labels), default=[], key="label_select")
            k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5, key="label_k")
 
        elif search_type == "trigger":
            search_query = st.selectbox("选择触发词", list(memory_manager.triggers), key="trigger_select")
            k = st.number_input("选择返回结果数量", min_value=1, max_value=100, value=5, key="trigger_k")
 
        search = {"search_query": search_query,
                  "search_type": search_type,
                  "k": k,
                  "labels": labels,
                  "exact_match": exact_match}
 
        # 展示和搜索记忆
        search_button = st.button("Search", icon="🔍", key="search_btn")
        add_memory = st.button("Add", icon="📂", key="add_memory_btn")
        
        # Label management
        st.write("Label Management")
        col1, col2 = st.columns(2)
        with col1:
            new_label = st.button("New", icon="🏷", key="new_label_btn")
            edit_label = st.button("Edit", icon="✏️", key="edit_label_btn")
        with col2:
            delete_label = st.button("Delete", icon="🗑️", key="delete_label_btn")
            spacer = st.empty()  # For alignment
            
        # Trigger management
        st.write("Trigger Management")
        col3, col4 = st.columns(2)
        with col3:
            new_trigger = st.button("New", icon="⚡", key="new_trigger_btn")
            edit_trigger = st.button("Edit", icon="✏️", key="edit_trigger_btn")
        with col4:
            delete_trigger = st.button("Delete", icon="🗑️", key="delete_trigger_btn")
            spacer2 = st.empty()  # For alignment
 
    return search, search_button, add_memory, new_label, new_trigger, edit_label, delete_label, edit_trigger, delete_trigger

 
def init_memory_management():
    # 初始化 MemoryManager 实例
    if 'memory_manager' not in st.session_state:
        st.session_state.memory_manager = MemoryManager()
    if 'memories' not in st.session_state:
        st.session_state.memories = (
            st.session_state.memory_manager.search_memory(query='', k=20, search_type="keyword"))
 
 
def main():
    # 初始化MemoryManager
    init_memory_management()
    memory_manager = st.session_state.memory_manager
    memories = st.session_state.memories
    # Streamlit 应用布局
    st.title("Memory Management Application")
 
    # 创建搜索和操作按钮
    search, search_button, add_memory, new_label, new_trigger, edit_label, delete_label, edit_trigger, delete_trigger = display_buttons(memory_manager)
 
    if search_button:
        st.session_state.memories = memory_manager.search_memory(search['search_query'],
                                                labels=search["labels"],
                                                k=search["k"],
                                                search_type=search["search_type"],
                                                exact_match=search["exact_match"])
        memories = st.session_state.memories
 
    if add_memory:
        add_memory_dialog()
 
    if new_label:
        add_label_dialog()
 
    if new_trigger:
        add_trigger_dialog()
 
    if edit_label:
        update_label_dialog()
 
    if delete_label:
        delete_label_dialog()
 
    if edit_trigger:
        update_trigger_dialog()
 
    if delete_trigger:
        delete_trigger_dialog()

    # 创建一个容器用于展示数据
    with st.container(border=True, key="content"):
        display_memories(memories, memory_manager)

if __name__ == "__main__":
    main()