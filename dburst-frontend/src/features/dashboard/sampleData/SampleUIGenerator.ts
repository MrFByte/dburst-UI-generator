export const generatedData = {
  project_id: "40bfe38d-f5a5-482d-b05f-3eeed83f3593",
  generation_id: "55302c3c-0cc4-4f66-a496-866555656627",
  schema: {
    type: "Container",
    class: "flex items-center justify-center h-screen",
    children: [
      {
        type: "Card",
        class: "p-4 rounded-lg bg-white shadow-md",
        children: [
          {
            type: "Text",
            class: "text-xl font-bold mb-4",
            content: "Login with a Smile :)",
          },
          {
            type: "Input",
            class: "p-2 rounded-lg border border-gray-300 mb-4",
            props: {
              placeholder: "Username",
            },
          },
          {
            type: "Input",
            class: "p-2 rounded-lg border border-gray-300 mb-4",
            props: {
              placeholder: "Password",
            },
          },
          {
            type: "Button",
            class: "p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-700",
            content: "Login",
          },
        ],
      },
    ],
  },
  code: `
import React from 'react';

export default function GeneratedUI() {
  return (
      <div className="flex items-center justify-center h-screen">
        <div className="p-4 rounded-lg bg-white shadow-md">
          <p className="text-xl font-bold mb-4">Login with a Smile :)</p>
          <input className="p-2 rounded-lg border border-gray-300 mb-4" placeholder="Username" />
          <input className="p-2 rounded-lg border border-gray-300 mb-4" placeholder="Password" />
          <button className="p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-700">Login</button>
        </div>
      </div>
  );
}
`,
  meta: {
    model: "llama-3.3-70b-versatile",
    usage: {
      queue_time: 0.058266599,
      prompt_tokens: 319,
      prompt_time: 0.01563828,
      completion_tokens: 241,
      completion_time: 0.478141471,
      total_tokens: 560,
      total_time: 0.493779751,
    },
  },
};

// export const generatedData = {"project_id":"c47c6927-cb71-4871-bb71-928fd0f5733f","generation_id":"90363054-0ac9-490b-b447-9d334f39424f","schema":{"type":"Container","class":"flex h-screen","children":[{"type":"Container","class":"w-64 bg-gray-800 p-4","children":[{"type":"Text","class":"text-lg text-white","content":"Dashboard"},{"type":"Button","class":"mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded","content":"New Item"}]},{"type":"Container","class":"flex-1 p-4","children":[{"type":"Container","class":"flex justify-between mb-4","children":[{"type":"Text","class":"text-2xl","content":"Dashboard"},{"type":"Button","class":"bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded","content":"New Item"}]},{"type":"Grid","class":"grid grid-cols-3 gap-4","props":{"cols":3},"children":[{"type":"Card","class":"bg-white p-4 rounded-lg shadow","children":[{"type":"Text","class":"text-lg","content":"Total Users"},{"type":"Text","class":"text-3xl","content":"1000"}]},{"type":"Card","class":"bg-white p-4 rounded-lg shadow","children":[{"type":"Text","class":"text-lg","content":"Total Sales"},{"type":"Text","class":"text-3xl","content":"$1000"}]},{"type":"Card","class":"bg-white p-4 rounded-lg shadow","children":[{"type":"Text","class":"text-lg","content":"Total Revenue"},{"type":"Text","class":"text-3xl","content":"$10000"}]}]},{"type":"Card","class":"bg-white p-4 rounded-lg shadow","children":[{"type":"Text","class":"text-lg","content":"Data Table"},{"type":"Grid","class":"grid grid-cols-4 gap-4","props":{"cols":4},"children":[{"type":"Text","class":"text-lg","content":"Name"},{"type":"Text","class":"text-lg","content":"Email"},{"type":"Text","class":"text-lg","content":"Phone"},{"type":"Text","class":"text-lg","content":"Address"}]},{"type":"Grid","class":"grid grid-cols-4 gap-4","props":{"cols":4},"children":[{"type":"Text","class":"text-lg","content":"John Doe"},{"type":"Text","class":"text-lg","content":"john@example.com"},{"type":"Text","class":"text-lg","content":"123-456-7890"},{"type":"Text","class":"text-lg","content":"123 Main St"}]}]}]}]},"code":"\nimport React from 'react';\n\nexport default function GeneratedUI() {\n  return (\n      <div className=\"flex h-screen\">\n        <div className=\"w-64 bg-gray-800 p-4\">\n          <p className=\"text-lg text-white\">Dashboard</p>\n          <button className=\"mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded\">New Item</button>\n        </div>\n        <div className=\"flex-1 p-4\">\n          <div className=\"flex justify-between mb-4\">\n            <p className=\"text-2xl\">Dashboard</p>\n            <button className=\"bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded\">New Item</button>\n          </div>\n          <div className=\"grid grid-cols-3 grid grid-cols-3 gap-4\">\n            <div className=\"bg-white p-4 rounded-lg shadow\">\n              <p className=\"text-lg\">Total Users</p>\n              <p className=\"text-3xl\">1000</p>\n            </div>\n            <div className=\"bg-white p-4 rounded-lg shadow\">\n              <p className=\"text-lg\">Total Sales</p>\n              <p className=\"text-3xl\">$1000</p>\n            </div>\n            <div className=\"bg-white p-4 rounded-lg shadow\">\n              <p className=\"text-lg\">Total Revenue</p>\n              <p className=\"text-3xl\">$10000</p>\n            </div>\n          </div>\n          <div className=\"bg-white p-4 rounded-lg shadow\">\n            <p className=\"text-lg\">Data Table</p>\n            <div className=\"grid grid-cols-4 grid grid-cols-4 gap-4\">\n              <p className=\"text-lg\">Name</p>\n              <p className=\"text-lg\">Email</p>\n              <p className=\"text-lg\">Phone</p>\n              <p className=\"text-lg\">Address</p>\n            </div>\n            <div className=\"grid grid-cols-4 grid grid-cols-4 gap-4\">\n              <p className=\"text-lg\">John Doe</p>\n              <p className=\"text-lg\">john@example.com</p>\n              <p className=\"text-lg\">123-456-7890</p>\n              <p className=\"text-lg\">123 Main St</p>\n            </div>\n          </div>\n        </div>\n      </div>\n  );\n}\n","meta":{"model":"llama-3.3-70b-versatile","usage":{"queue_time":0.057316507,"prompt_tokens":329,"prompt_time":0.016681893,"completion_tokens":962,"completion_time":1.725374269,"total_tokens":1291,"total_time":1.742056162}}}
