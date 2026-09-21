// ============================================================
// 前端交互逻辑（这个文件运行在浏览器里，不是服务器里）
// 负责：向后端发请求要数据 -> 拿到数据后更新页面显示
// ============================================================

let currentQuestionId = null;
let currentType = null;

// TODO 1：页面一打开，就问后端要第一题
window.addEventListener("DOMContentLoaded", () => {
  fetch("/api/start", { method: "POST" })
    .then(res => res.json())
    .then(renderStep);
});

// TODO 2：点提交按钮时，把用户答案发给后端
document.getElementById("submitBtn").addEventListener("click", () => {
  let userAnswer;

  // 在这里判断是客观题还是开放题，分别获取用户填的答案
  // 客观题：document.querySelector('input[name="option"]:checked')
  // 开放题：document.getElementById("openAnswerBox").value

  fetch("/api/answer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question_id: currentQuestionId, answer: userAnswer })
  })
    .then(res => res.json())
    .then(data => {
      // 在这里先显示上一题的反馈（data.last_score, data.last_feedback）
      // 如果 data.finished 为 true，跳转到 /report
      // 否则调用 renderStep(data) 显示下一题
    });
});

// TODO 3：把后端返回的题目数据，显示到页面上
function renderStep(data) {
  // 在这里把 data.text（题干）、data.options（选项）等
  // 填充到 index.html 里对应的元素上
  // 记得根据 data.type 判断是显示选择题还是显示文本输入框
}