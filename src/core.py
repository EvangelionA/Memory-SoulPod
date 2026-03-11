import asyncio
from litellm import acompletion
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

console = Console()

# 1. 记忆克隆：在这里定义“朋友”的性格、背景和说话习惯
SYSTEM_PROMPT = """
你现在克隆了我的好朋友'小杰'。
性格特点：幽默、爱吐槽但很关心人，说话随性，经常用'哈'、'没准儿'。
背景：我们是高中同学，都喜欢科幻电影。
注意：保持回复简短，像聊天软件一样对话，不要像 AI 助手。
"""

async def chat_with_friend():
    # 历史记录：存储对话上下文
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    console.print("[bold green]已连接到克隆记忆：小杰 (输入 'exit' 退出)[/bold green]\n")

    while True:
        user_input = console.input("[bold blue]我: [/bold blue]")
        if user_input.lower() in ["exit", "quit", "退出"]:
            break

        messages.append({"role": "user", "content": user_input})
        
        # 使用 Rich 的 Live 模式实现流式刷新
        full_response = ""
        console.print("[bold magenta]小杰: [/bold magenta]", end="")
        
        with Live(display_handle=True) as live:
            # 2. 异步流式调用
            response = await acompletion(
                model="ollama/llama3", # 确保你本地已经 ollama run llama3
                messages=messages,
                stream=True,
                api_base="http://localhost:11434" 
            )

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    # 实时渲染 Markdown，让对话看起来更舒服
                    live.update(Markdown(full_response))

        # 3. 将 AI 的回复存入记忆
        messages.append({"role": "assistant", "content": full_response})


async def get_reply(messages: list[dict], stream: bool = False) -> str:
    """
    供 HTTP API 调用：根据已有对话历史请求一次模型回复。
    messages 为 [{"role":"user"|"assistant","content":"..."}, ...]，不含 system。
    """
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(messages)
    if stream:
        response = await acompletion(
            model="ollama/llama3",
            messages=full_messages,
            stream=True,
            api_base="http://localhost:11434",
        )
        full_response = ""
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
        return full_response
    response = await acompletion(
        model="ollama/qwen3:8b",
        messages=full_messages,
        stream=False,
        api_base="http://localhost:11434",
    )
    return (response.choices[0].message.content or "").strip()


if __name__ == "__main__":
    try:
        asyncio.run(chat_with_friend())
    except KeyboardInterrupt:
        console.print("\n[red]对话强制结束。[/red]")