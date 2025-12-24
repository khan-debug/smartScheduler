// Management page JavaScript - handles CRUD operations for Users, Courses, and Rooms
document.addEventListener('DOMContentLoaded', (event) => {
    // Get configuration from inline script
    const addModal = document.getElementById("addModal");
    const editModal = document.getElementById("editModal");
    const deleteConfirmModal = document.getElementById("deleteConfirmModal");

    const addBtn = document.getElementById("addBtn");

    const addClose = document.getElementById("addClose");
    const editClose = document.getElementById("editClose");

    const itemList = document.querySelector("#itemList tbody");
    const addUrl = MANAGEMENT_CONFIG.addUrl;
    const getUrl = MANAGEMENT_CONFIG.getUrl;
    const itemName = MANAGEMENT_CONFIG.itemName;
    const formFields = MANAGEMENT_CONFIG.formFields;
    const fromDashboard = MANAGEMENT_CONFIG.fromDashboard;

    function togglePasswordVisibility(inputId, toggleId) {
        const input = document.getElementById(inputId);
        const icon = document.getElementById(toggleId);
        if (input.type === "password") {
            input.type = "text";
            icon.classList.remove("fa-eye-slash");
            icon.classList.add("fa-eye");
        } else {
            input.type = "password";
            icon.classList.remove("fa-eye");
            icon.classList.add("fa-eye-slash");
        }
    }

    if (document.getElementById('toggle_password')) {
        document.getElementById('toggle_password').addEventListener('click', () => togglePasswordVisibility('password', 'toggle_password'));
    }
    if (document.getElementById('toggle_confirm_password')) {
        document.getElementById('toggle_confirm_password').addEventListener('click', () => togglePasswordVisibility('confirm_password', 'toggle_confirm_password'));
    }
    if (document.getElementById('toggle_edit_password')) {
        document.getElementById('toggle_edit_password').addEventListener('click', () => togglePasswordVisibility('edit_password', 'toggle_edit_password'));
    }
    if (document.getElementById('toggle_edit_confirm_password')) {
        document.getElementById('toggle_edit_confirm_password').addEventListener('click', () => togglePasswordVisibility('edit_confirm_password', 'toggle_edit_confirm_password'));
    }

    function fetchItems() {
        fetch(getUrl)
            .then(response => response.json())
            .then(data => {
                itemList.innerHTML = ""; // Clear existing table body content
                data.items.forEach((item, index) => {
                    const tr = document.createElement("tr");
                    let rowHtml = `<td>${index + 1}</td>`;
                    formFields.forEach(field => {
                        if (field.table_display) {
                            rowHtml += `<td>${item[field.name] || ''}</td>`;
                        }
                    });
                    if (!fromDashboard) {
                        rowHtml += `
                            <td>
                                <button class="action-btn edit" data-id="${index}"><i class="fas fa-pencil-alt"></i></button>
                                <button class="action-btn delete" data-id="${index}"><i class="fas fa-trash-alt"></i></button>
                            </td>
                        `;
                    }
                    tr.innerHTML = rowHtml;
                    itemList.appendChild(tr);
                });

                if (!fromDashboard) {
                    // Add event listeners for edit and delete buttons
                    document.querySelectorAll('.edit').forEach(button => {
                        button.addEventListener('click', handleEdit);
                    });
                    document.querySelectorAll('.delete').forEach(button => {
                        button.addEventListener('click', handleDelete);
                    });
                }
            });
    }

    function handleEdit(event) {
        const itemId = event.currentTarget.dataset.id;
        fetch(`/get_item/${itemName}/${itemId}`)
            .then(response => response.json())
            .then(item => {
                document.getElementById('editItemId').value = itemId;
                formFields.forEach(field => {
                    if (field.name === "floor_number") {
                        document.getElementById(`edit_${field.name}`).value = item[field.name] || '';
                        document.getElementById(`edit_${field.name}`).readOnly = true; // Make it read-only
                    } else if (field.type === "select") {
                        const selectElement = document.getElementById(`edit_${field.name}`);
                        if (selectElement) {
                            selectElement.value = item[field.name] || '';
                        }
                    }
                    else {
                        document.getElementById(`edit_${field.name}`).value = item[field.name] || '';
                    }
                });
                editModal.style.display = "block";
            });
    }

    function handleDelete(event) {
        const itemId = event.currentTarget.dataset.id;
        deleteConfirmModal.style.display = "block";

        document.getElementById('confirmDelete').onclick = function() {
            fetch(`/delete_item/${itemName}/${itemId}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        fetchItems();
                        deleteConfirmModal.style.display = "none";
                    }
                });
        }

        document.getElementById('cancelDelete').onclick = function() {
            deleteConfirmModal.style.display = "none";
        }
    }

    if (addBtn) {
        addBtn.onclick = function() {
            addModal.style.display = "block";
        }
    }

    addClose.onclick = function() {
        addModal.style.display = "none";
    }

    editClose.onclick = function() {
        editModal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == addModal) {
            addModal.style.display = "none";
        }
        if (event.target == editModal) {
            editModal.style.display = "none";
        }
        if (event.target == deleteConfirmModal) {
            deleteConfirmModal.style.display = "none";
        }
    }

    if (addBtn) {
        document.getElementById("addForm").onsubmit = function(event) {
            event.preventDefault();

            // Only validate password if password fields exist (for Users only)
            const passwordField = document.getElementById("password");
            const confirmPasswordField = document.getElementById("confirm_password");
            const errorDiv = document.getElementById("password_error");

            if (passwordField && confirmPasswordField) {
                const password = passwordField.value;
                const confirm_password = confirmPasswordField.value;

                if (password !== confirm_password) {
                    if (errorDiv) errorDiv.style.display = "block";
                    return;
                } else {
                    if (errorDiv) errorDiv.style.display = "none";
                }
            }

            const data = {};
            formFields.forEach(field => {
                if (field.form_display) {
                    data[field.name] = document.getElementById(field.name).value;
                }
            });

            fetch(addUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetchItems();
                    addModal.style.display = "none";
                    document.getElementById("addForm").reset();
                } else {
                    // Show error message
                    alert("Error: " + (data.error || "Failed to create user"));
                }
            })
            .catch(error => {
                alert("Error: Failed to communicate with server");
                console.error('Error:', error);
            });
        }
    }

    document.getElementById("editForm").onsubmit = function(event) {
        event.preventDefault();

        // Only validate password if password fields exist (for Users only)
        const passwordField = document.getElementById("edit_password");
        const confirmPasswordField = document.getElementById("edit_confirm_password");
        const errorDiv = document.getElementById("edit_password_error");

        if (passwordField && confirmPasswordField) {
            const password = passwordField.value;
            const confirm_password = confirmPasswordField.value;

            if (password !== confirm_password) {
                if (errorDiv) errorDiv.style.display = "block";
                return;
            } else {
                if (errorDiv) errorDiv.style.display = "none";
            }
        }

        const itemId = document.getElementById('editItemId').value;
        const data = {};
        formFields.forEach(field => {
            if (field.form_display) {
                data[field.name] = document.getElementById(`edit_${field.name}`).value;
            }
        });

        fetch(`/update_item/${itemName}/${itemId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                fetchItems();
                editModal.style.display = "none";
            } else {
                // Show error message
                alert("Error: " + (data.error || "Failed to update user"));
            }
        })
        .catch(error => {
            alert("Error: Failed to communicate with server");
            console.error('Error:', error);
        });
    }

    // Fetch items when the page loads
    fetchItems();
});
