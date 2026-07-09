from __future__ import annotations

import html

import pandas as pd
import streamlit as st

import api_client as api
from components.chat_box import render_messages


st.set_page_config(page_title="LLM Chat-bot", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: #ffffff;
    }
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        display: none !important;
        height: 0 !important;
    }
    [data-testid="stSidebar"] {
        background: #f7f7f4;
        border-right: 1px solid #e6e3dc;
        position: relative;
        width: 21rem !important;
        min-width: 21rem !important;
        top: 0 !important;
        height: 100vh !important;
    }
    [data-testid="stSidebarNav"] {
        display: none;
    }
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    section[data-testid="stSidebar"] button[title^="Collapse"],
    section[data-testid="stSidebar"] button[aria-label^="Collapse"],
    section[data-testid="stSidebar"] button[data-testid*="baseButton-header"] {
        display: none !important;
    }
    [data-testid="stSidebarContent"] {
        padding: 0.6rem 0.85rem 5.6rem 0.85rem !important;
        margin-top: 0 !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding: 0.6rem 0.85rem 5.6rem 0.85rem !important;
        margin-top: 0 !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    [data-testid="stSidebarContent"] > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .block-container {
        max-width: 980px;
        padding-top: 1.4rem;
        padding-bottom: 7.5rem;
    }
    .sidebar-title {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        font-size: 1.24rem;
        font-weight: 760;
        color: #1f2937;
        padding: 0;
        height: 2.25rem;
        line-height: 2.25rem;
        white-space: nowrap;
        margin-top: 0 !important;
    }
    .sidebar-user {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 21rem;
        max-width: 21rem;
        box-sizing: border-box;
        min-height: 3.35rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.65rem 1.25rem;
        border-top: 1px solid #e6e3dc;
        background: #f7f7f4;
        color: #202123;
        z-index: 10;
    }
    .sidebar-avatar {
        width: 2rem;
        height: 2rem;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #334155;
        color: #ffffff;
        font-size: 0.72rem;
        letter-spacing: 0;
        flex: 0 0 auto;
    }
    .sidebar-username {
        font-size: 0.98rem;
        font-weight: 560;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }
    .sidebar-section {
        color: #111827;
        font-size: 0.84rem;
        font-weight: 720;
        margin: 0;
        line-height: 2.25rem;
    }
    .sidebar-chat-header {
        margin-top: 1.1rem;
    }
    .sidebar-static-icon {
        min-height: 2.25rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #8a8d91;
        border-radius: 8px;
        background: transparent;
    }
    .sidebar-static-icon::before {
        content: "";
        width: 1.05rem;
        height: 1.05rem;
        border: 1.8px solid #8a8d91;
        border-radius: 5px;
        box-sizing: border-box;
        background:
            linear-gradient(to right, transparent 0 58%, #8a8d91 58% 68%, transparent 68% 100%);
    }
    .sidebar-static-icon:hover {
        background: #ecebe8;
    }
    .sidebar-menu-card {
        min-width: 13rem;
        padding: 0.25rem;
    }
    .menu-hint {
        color: #71717a;
        font-size: 0.82rem;
        padding: 0 0.3rem 0.35rem 0.3rem;
    }
    .muted {
        color: #777d86;
        font-size: 0.88rem;
    }
    .main-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.4rem;
    }
    .conversation-title {
        font-size: 0.96rem;
        color: #6b7280;
        max-width: 520px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .empty-hero {
        min-height: 42vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }
    .empty-hero h1 {
        font-size: 1.7rem;
        line-height: 1.35;
        margin: 0 0 1.5rem 0;
        font-weight: 650;
        color: #111827;
    }
    .stats-card {
        border: 1px solid #ebe7df;
        background: #ffffff;
        border-radius: 8px;
        padding: 1rem;
    }
    section[data-testid="stSidebar"] button,
    .stButton > button,
    .stDownloadButton > button,
    .stLinkButton > a {
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] button {
        border: 0 !important;
        border-color: transparent !important;
        background: transparent !important;
        box-shadow: none !important;
        min-height: 2.25rem;
        width: 100% !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background: #ecebe8 !important;
    }
    section[data-testid="stSidebar"] button:focus,
    section[data-testid="stSidebar"] button:active {
        border-color: transparent !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] button:disabled {
        border: 0 !important;
        background: transparent !important;
        color: #8a8d91 !important;
        opacity: 1 !important;
    }
    div[data-testid="stPopover"] button {
        border: 0 !important;
        background: transparent !important;
        color: #737373 !important;
        box-shadow: none !important;
    }
    div[data-testid="stPopover"] > button svg,
    div[data-testid="stPopover"] button[aria-haspopup="dialog"] svg {
        display: none !important;
    }
    div[data-testid="stPopover"] > button::after,
    div[data-testid="stPopover"] button[aria-haspopup="dialog"]::after {
        content: none !important;
        display: none !important;
    }
    div[data-testid="stPopover"] button:hover {
        background: #ecebe8 !important;
        color: #111827 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div[data-testid="stPopover"] {
        opacity: 0;
        transition: opacity 120ms ease;
        pointer-events: none;
    }
    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]:hover div[data-testid="stPopover"] {
        opacity: 1;
        pointer-events: auto;
    }
    section[data-testid="stSidebar"] .stButton > button {
        justify-content: flex-start;
        border: 0 !important;
        background: transparent !important;
        color: #202123;
        min-height: 2.25rem;
        width: 100% !important;
        padding-left: 0.55rem;
        padding-right: 0.55rem;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button p {
        width: 100%;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] .stButton > button div {
        width: 100% !important;
        justify-content: flex-start !important;
    }
    section[data-testid="stSidebar"] button[title*="搜索聊天"] p {
        font-size: 1.55rem !important;
        line-height: 1 !important;
        text-align: center !important;
        color: #202123 !important;
    }
    section[data-testid="stSidebar"] button[title*="搜索聊天"] {
        justify-content: center !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #ecebe8 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:disabled {
        border: 0 !important;
        background: transparent !important;
        color: #8a8d91 !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #ecebe8 !important;
        color: #111827;
    }
    .sidebar-top-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 2.25rem 2.25rem;
        align-items: center;
        column-gap: 0.45rem;
        margin-top: -3.75rem;
        margin-bottom: 0.35rem;
    }
    [data-testid="stSidebar"] a.sidebar-icon-link,
    [data-testid="stSidebar"] a.sidebar-icon-link:visited,
    [data-testid="stSidebar"] a.sidebar-icon-link:hover,
    [data-testid="stSidebar"] a.sidebar-icon-link:active,
    .sidebar-icon-static {
        width: 2.25rem;
        height: 2.25rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        color: #202123 !important;
        text-decoration: none !important;
        -webkit-text-decoration: none !important;
        border: 0 !important;
        border-bottom: 0 !important;
        box-shadow: none !important;
        background: transparent;
        box-sizing: border-box;
    }
    [data-testid="stSidebar"] a.sidebar-icon-link {
        font-size: 1.55rem;
        line-height: 1;
    }
    [data-testid="stSidebar"] a.sidebar-icon-link:hover,
    .sidebar-icon-static:hover {
        background: #ecebe8;
        text-decoration: none !important;
        -webkit-text-decoration: none !important;
        color: #202123 !important;
    }
    .sidebar-icon-static::before {
        content: "";
        width: 1.05rem;
        height: 1.05rem;
        border: 1.8px solid #8a8d91;
        border-radius: 5px;
        box-sizing: border-box;
        background:
            linear-gradient(to right, transparent 0 58%, #8a8d91 58% 68%, transparent 68% 100%);
    }
    [data-testid="stSidebar"] a.sidebar-nav-link,
    [data-testid="stSidebar"] a.sidebar-nav-link:visited,
    [data-testid="stSidebar"] a.sidebar-nav-link:hover,
    [data-testid="stSidebar"] a.sidebar-nav-link:active {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        min-height: 2.35rem;
        padding: 0 0.55rem;
        border-radius: 8px;
        color: #202123 !important;
        text-decoration: none !important;
        -webkit-text-decoration: none !important;
        border: 0 !important;
        border-bottom: 0 !important;
        box-shadow: none !important;
        font-size: 1.08rem;
        font-weight: 560;
    }
    [data-testid="stSidebar"] a.sidebar-nav-link:hover {
        background: #ecebe8;
        color: #202123 !important;
        text-decoration: none !important;
        -webkit-text-decoration: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a.sidebar-icon-link,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a.sidebar-nav-link {
        color: #202123 !important;
        text-decoration: none !important;
        -webkit-text-decoration: none !important;
        border: 0 !important;
        border-bottom: 0 !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .element-container:has(#sidebar-user-anchor) {
        margin-top: 0 !important;
        width: 100% !important;
        height: 0 !important;
        padding-top: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def state_default(key: str, value) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


state_default("user", None)
state_default("user_id", None)
state_default("conversation_id", None)
state_default("models", [])
state_default("prompts", [])
state_default("conversations", [])
state_default("selected_model", "mock")
state_default("selected_prompt", "通用助手")
state_default("view", "chat")
state_default("show_search", False)
state_default("search_keyword", "")


nav_action = st.query_params.get("nav")
if nav_action == "search":
    st.session_state.show_search = not st.session_state.show_search
    st.query_params.clear()
elif nav_action == "stats":
    st.session_state.view = "stats"
    st.query_params.clear()


def refresh_options() -> None:
    st.session_state.models = api.list_models()
    st.session_state.prompts = api.list_prompts()
    model_names = [item["name"] for item in st.session_state.models]
    prompt_names = [item["name"] for item in st.session_state.prompts]
    if model_names and st.session_state.selected_model not in model_names:
        st.session_state.selected_model = "mock" if "mock" in model_names else model_names[0]
    if prompt_names and st.session_state.selected_prompt not in prompt_names:
        st.session_state.selected_prompt = "通用助手" if "通用助手" in prompt_names else prompt_names[0]


def refresh_conversations() -> None:
    if st.session_state.user_id:
        st.session_state.conversations = api.list_conversations(st.session_state.user_id)


def create_new_conversation() -> None:
    created = api.create_conversation(
        st.session_state.user_id,
        st.session_state.selected_model,
        st.session_state.selected_prompt,
    )
    st.session_state.conversation_id = created["conversation_id"]
    st.session_state.view = "chat"
    refresh_conversations()


def ensure_conversation() -> int:
    if st.session_state.conversation_id:
        return st.session_state.conversation_id
    create_new_conversation()
    return st.session_state.conversation_id


def load_current_conversation() -> dict | None:
    if not st.session_state.conversation_id or not st.session_state.user_id:
        return None
    return api.get_conversation(st.session_state.conversation_id, st.session_state.user_id)


def model_names() -> list[str]:
    return [item["name"] for item in st.session_state.models] or ["mock"]


def prompt_names() -> list[str]:
    return [item["name"] for item in st.session_state.prompts] or ["通用助手"]


def select_conversation(conversation_id: int) -> None:
    st.session_state.conversation_id = conversation_id
    st.session_state.view = "chat"


def render_login() -> None:
    st.markdown("<div class='empty-hero'><h1>LLM Chat-bot</h1></div>", unsafe_allow_html=True)
    username = st.text_input("用户名", value="test_user")
    if st.button("进入系统", type="primary", use_container_width=True):
        try:
            user = api.create_user(username)
            st.session_state.user = user
            st.session_state.user_id = user["id"]
            refresh_conversations()
            st.rerun()
        except api.ApiError as exc:
            st.error(str(exc))


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-top-row">
                <div class="sidebar-title">LLM Chat-bot</div>
                <a class="sidebar-icon-link" href="?nav=search" target="_self" title="搜索聊天  Ctrl + K">⌕</a>
                <span class="sidebar-icon-static" title="收起侧边栏"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.show_search:
            st.session_state.search_keyword = st.text_input(
                "搜索",
                value=st.session_state.search_keyword,
                placeholder="搜索会话...",
                label_visibility="collapsed",
            )
            if st.session_state.search_keyword:
                try:
                    results = api.search_conversations(st.session_state.user_id, st.session_state.search_keyword)
                except api.ApiError as exc:
                    st.error(str(exc))
                    results = []
                for item in results:
                    if st.button(
                        item["title"],
                        key=f"search-result-{item['conversation_id']}",
                        use_container_width=True,
                    ):
                        select_conversation(item["conversation_id"])
                        st.rerun()

        st.markdown(
            '<a class="sidebar-nav-link" href="?nav=stats" target="_self">◷&nbsp;&nbsp;统计</a>',
            unsafe_allow_html=True,
        )

        chat_header = st.columns([0.82, 0.18], vertical_alignment="center")
        with chat_header[0]:
            st.markdown("<div class='sidebar-section sidebar-chat-label'>聊天</div>", unsafe_allow_html=True)
        with chat_header[1]:
            if st.button("✎", key="new-chat-in-section", help="新聊天", use_container_width=True):
                create_new_conversation()
                st.rerun()
        if not st.session_state.conversations:
            st.markdown("<span class='muted'>暂无会话</span>", unsafe_allow_html=True)

        for item in st.session_state.conversations:
            row = st.columns([0.82, 0.18], vertical_alignment="center")
            is_current = st.session_state.conversation_id == item["conversation_id"]
            with row[0]:
                if st.button(
                    f"{'· ' if is_current and st.session_state.view == 'chat' else ''}{item['title']}",
                    key=f"conversation-{item['conversation_id']}",
                    use_container_width=True,
                ):
                    select_conversation(item["conversation_id"])
                    st.rerun()
            with row[1]:
                with st.popover("⋯", help="会话操作", use_container_width=True):
                    st.markdown("<div class='sidebar-menu-card'>", unsafe_allow_html=True)
                    st.link_button(
                        "↥ 分享",
                        api.export_url(item["conversation_id"], st.session_state.user_id, "markdown"),
                        use_container_width=True,
                    )
                    if st.button("＋ 开始群聊", key=f"group-chat-{item['conversation_id']}", use_container_width=True):
                        st.toast("当前版本使用单人会话模式")
                    new_title = st.text_input(
                        "✎ 重命名",
                        value=item["title"],
                        key=f"rename-{item['conversation_id']}",
                    )
                    if st.button("保存重命名", key=f"save-title-{item['conversation_id']}", use_container_width=True):
                        api.rename_conversation(item["conversation_id"], st.session_state.user_id, new_title)
                        refresh_conversations()
                        st.rerun()
                    st.link_button(
                        "▣ 导出 TXT",
                        api.export_url(item["conversation_id"], st.session_state.user_id, "txt"),
                        use_container_width=True,
                    )
                    st.link_button(
                        "▤ 导出 JSON",
                        api.export_url(item["conversation_id"], st.session_state.user_id, "json"),
                        use_container_width=True,
                    )
                    if st.button("◆ 保存会话", key=f"save-conversation-{item['conversation_id']}", use_container_width=True):
                        st.toast("会话已自动保存到数据库")
                    if st.button("▥ 归档", key=f"archive-{item['conversation_id']}", use_container_width=True):
                        api.archive_conversation(item["conversation_id"], st.session_state.user_id)
                        if st.session_state.conversation_id == item["conversation_id"]:
                            st.session_state.conversation_id = None
                        refresh_conversations()
                        st.rerun()
                    if st.button("⌫ 删除", key=f"delete-{item['conversation_id']}", use_container_width=True):
                        api.archive_conversation(item["conversation_id"], st.session_state.user_id)
                        if st.session_state.conversation_id == item["conversation_id"]:
                            st.session_state.conversation_id = None
                        refresh_conversations()
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        username = html.escape(st.session_state.user["username"] if st.session_state.user else "")
        initials = html.escape((username[:2] or "U").upper())
        st.markdown(
            "<span id='sidebar-user-anchor'></span>"
            f"<div class='sidebar-user'><span class='sidebar-avatar'>{initials}</span>"
            f"<span class='sidebar-username'>{username}</span></div>",
            unsafe_allow_html=True,
        )


def sync_conversation_settings(conversation: dict | None) -> None:
    if not conversation:
        return
    if conversation["model_name"] != st.session_state.selected_model:
        api.update_conversation_model(
            conversation["conversation_id"],
            st.session_state.user_id,
            st.session_state.selected_model,
        )
    if conversation["prompt_role"] != st.session_state.selected_prompt:
        api.update_conversation_prompt_role(
            conversation["conversation_id"],
            st.session_state.user_id,
            st.session_state.selected_prompt,
        )


def render_topbar(conversation: dict | None = None) -> None:
    left, center, right = st.columns([0.25, 0.48, 0.27], vertical_alignment="center")
    with left:
        names = model_names()
        st.session_state.selected_model = st.selectbox(
            "当前模型",
            names,
            index=names.index(st.session_state.selected_model) if st.session_state.selected_model in names else 0,
            label_visibility="collapsed",
        )
    with center:
        title = conversation["title"] if conversation else "准备好了，随时开始"
        st.markdown(f"<div class='conversation-title'>{title}</div>", unsafe_allow_html=True)
    with right:
        prompts = prompt_names()
        st.session_state.selected_prompt = st.selectbox(
            "Prompt 角色",
            prompts,
            index=prompts.index(st.session_state.selected_prompt) if st.session_state.selected_prompt in prompts else 0,
            label_visibility="collapsed",
        )


def render_chat_view() -> None:
    conversation = load_current_conversation()
    render_topbar(conversation)
    sync_conversation_settings(conversation)

    if conversation and conversation["messages"]:
        render_messages(conversation["messages"])
    else:
        st.markdown(
            "<div class='empty-hero'><h1>准备好了，随时开始</h1><p class='muted'>选择模型和角色后，直接在下方输入消息。</p></div>",
            unsafe_allow_html=True,
        )

    user_message = st.chat_input("有问题，尽管问")
    if user_message:
        conversation_id = ensure_conversation()
        with st.chat_message("user"):
            st.markdown(user_message)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            answer = ""
            try:
                for chunk in api.stream_chat(
                    st.session_state.user_id,
                    conversation_id,
                    user_message,
                    st.session_state.selected_model,
                    st.session_state.selected_prompt,
                ):
                    answer += chunk
                    placeholder.markdown(answer)
            except api.ApiError as exc:
                st.error(str(exc))
        refresh_conversations()
        st.rerun()


def render_stats_view() -> None:
    render_topbar(None)
    try:
        stats = api.get_stats(st.session_state.user_id)
    except api.ApiError as exc:
        st.error(str(exc))
        return

    st.subheader("统计")
    metric_cols = st.columns(2)
    with metric_cols[0]:
        st.metric("会话数", stats["conversation_count"])
    with metric_cols[1]:
        st.metric("消息数", stats["message_count"])

    col_model, col_role = st.columns(2)
    with col_model:
        st.markdown("#### 模型使用")
        if stats["model_usage"]:
            st.bar_chart(pd.Series(stats["model_usage"]))
        else:
            st.caption("暂无数据")
    with col_role:
        st.markdown("#### 角色使用")
        if stats["prompt_role_usage"]:
            st.bar_chart(pd.Series(stats["prompt_role_usage"]))
        else:
            st.caption("暂无数据")

    st.markdown("#### 最近 7 天")
    st.line_chart(pd.Series(stats["recent_7_days"]))

    st.markdown("#### 活跃会话")
    st.dataframe(pd.DataFrame(stats["active_conversations"]), use_container_width=True, hide_index=True)


try:
    refresh_options()
except api.ApiError as exc:
    st.error(str(exc))
    st.stop()

if not st.session_state.user_id:
    render_login()
    st.stop()

refresh_conversations()
render_sidebar()

if st.session_state.view == "stats":
    render_stats_view()
else:
    render_chat_view()
