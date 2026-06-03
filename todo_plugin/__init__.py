class Plugin:
    name = "Todo App"
    slug = "todo-plugin"
    version = "1.0"
    description = "A simple todo list plugin"

    def render(self, request, config):
        html = """
        <div class="max-w-2xl mx-auto">
            <h2 class="text-2xl font-bold mb-6">Todo List</h2>
            <div class="mb-6">
                <input type="text" id="todoInput" placeholder="Add a new todo..." 
                       class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <button onclick="addTodo()" 
                        class="mt-2 w-full sm:w-auto bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                    Add Todo
                </button>
            </div>
            <ul id="todoList" class="space-y-2">
            </ul>
        </div>
        <script>
            let todos = JSON.parse(localStorage.getItem('todos') || '[]');

            function renderTodos() {
                const list = document.getElementById('todoList');
                list.innerHTML = '';
                todos.forEach((todo, index) => {
                    const li = document.createElement('li');
                    li.className = 'flex items-center justify-between bg-gray-50 p-4 rounded-md';
                    let todoText = todo.completed ? 
                        '<span class="line-through text-gray-500">' + todo.text + '</span>' : 
                        '<span>' + todo.text + '</span>';
                    let btnText = todo.completed ? 'Undo' : 'Complete';
                    li.innerHTML = todoText + '\
                        <div class="flex flex-col sm:flex-row gap-2 mt-2 sm:mt-0">\
                            <button onclick="toggleTodo(' + index + ')" class="text-green-600 hover:text-green-800 text-sm">'+btnText+'</button>\
                            <button onclick="deleteTodo(' + index + ')" class="text-red-600 hover:text-red-800 text-sm">Delete</button>\
                        </div>';
                    list.appendChild(li);
                });
            }

            function addTodo() {
                const input = document.getElementById('todoInput');
                if (input.value.trim()) {
                    todos.push({ text: input.value.trim(), completed: false });
                    input.value = '';
                    saveTodos();
                    renderTodos();
                }
            }

            function toggleTodo(index) {
                todos[index].completed = !todos[index].completed;
                saveTodos();
                renderTodos();
            }

            function deleteTodo(index) {
                todos.splice(index, 1);
                saveTodos();
                renderTodos();
            }

            function saveTodos() {
                localStorage.setItem('todos', JSON.stringify(todos));
            }

            // Add Enter key support
            document.getElementById('todoInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    addTodo();
                }
            });

            renderTodos();
        </script>
        """
        return html
