import streamlit as st

def interactive(input_string: str) -> str:
    """Get user interaction through radio buttons
    
    Args:
        input_string: The input string to display
        
    Returns:
        Modified string if user chooses to modify, original string if approved,
        or None if terminated
    """
    # Initialize counter in session state if not exists
    if 'interactive_counter' not in st.session_state:
        st.session_state.interactive_counter = 0
    
    # Get a unique key for this instance
    instance_key = st.session_state.interactive_counter
    st.session_state.interactive_counter += 1
    
    # Create radio buttons for user interaction
    action = st.radio("选择操作", ["Please select an action:", "通过", "修改", "终止"], horizontal=True, key=f"action_{instance_key}", 
        captions=["", "I'm satisfied with the result", "I would like to modify the result", "I'd like to terminate"])
    
    if action == "通过":
        return input_string
    elif action == "修改":
        # Allow user to modify the input string via text input box
        modified_string = st.text_input('修改内容:', value=input_string, key=f"input_{instance_key}")
        if st.button('确认修改', key=f"confirm_{instance_key}"):
            return modified_string
    elif action == "终止":
        return None