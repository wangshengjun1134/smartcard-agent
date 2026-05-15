import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";

function App() {
  const [greeting, setGreeting] = useState("");
  const [name, setName] = useState("");

  async function greet() {
    // Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
    setGreeting(await invoke("greet", { name }));
  }

  return (
    <div className="container">
      <h1>SmartcardAgent</h1>
      <p>智能卡知识库代理</p>

      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          greet();
        }}
      >
        <input
          id="greet-input"
          onChange={(e) => setName(e.currentTarget.value)}
          placeholder="输入您的名字..."
        />
        <button type="submit">问候</button>
      </form>

      <p>{greeting}</p>
    </div>
  );
}

export default App;