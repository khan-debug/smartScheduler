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
                            // Inline dropdown for Type field (Lab/Lecture Hall)
                            if (field.name === 'type' && itemName === 'room') {
                                const roomType = item[field.name] || 'Lab';
                                const typeClass = roomType === 'Lab' ? 'type-lab' : 'type-lecture';

                                rowHtml += `
                                    <td>
                                        <select class="type-dropdown ${typeClass}" data-room-id="${index}" data-current-value="${roomType}">
                                            <option value="Lab" ${roomType === 'Lab' ? 'selected' : ''}>Lab</option>
                                            <option value="Lecture Hall" ${roomType === 'Lecture Hall' ? 'selected' : ''}>Lecture Hall</option>
                                        </select>
                                    </td>
                                `;
                            }
                            // Inline dropdown for availability field
                            else if (field.name === 'availability') {
                                const availability = item[field.name] || 'Available';
                                const statusClass = availability === 'Not Available' ? 'status-not-available' : 'status-available';

                                rowHtml += `
                                    <td>
                                        <select class="availability-dropdown ${statusClass}" data-room-id="${index}" data-current-value="${availability}">
                                            <option value="Available" ${availability === 'Available' ? 'selected' : ''}>Available</option>
                                            <option value="Not Available" ${availability === 'Not Available' ? 'selected' : ''}>Not Available</option>
                                        </select>
                                    </td>
                                `;
                            } else {
                                rowHtml += `<td>${item[field.name] || ''}</td>`;
                            }
                        }
                    });
                    if (!fromDashboard) {
                        // Only show delete button for rooms (edit is inline now)
                        if (itemName === 'room') {
                            rowHtml += `
                                <td>
                                    <button class="action-btn delete" data-id="${index}"><i class="fas fa-trash-alt"></i></button>
                                </td>
                            `;
                        } else {
                            // For non-room items, keep both edit and delete
                            rowHtml += `
                                <td>
                                    <button class="action-btn edit" data-id="${index}"><i class="fas fa-pencil-alt"></i></button>
                                    <button class="action-btn delete" data-id="${index}"><i class="fas fa-trash-alt"></i></button>
                                </td>
                            `;
                        }
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

                // Add event listeners for type dropdowns (rooms only)
                document.querySelectorAll('.type-dropdown').forEach(dropdown => {
                    dropdown.addEventListener('change', handleTypeChange);
                });

                // Add event listeners for availability dropdowns
                document.querySelectorAll('.availability-dropdown').forEach(dropdown => {
                    dropdown.addEventListener('change', handleAvailabilityChange);
                });
            });
    }

    function handleTypeChange(event) {
        const dropdown = event.target;
        const roomId = dropdown.dataset.roomId;
        const newType = dropdown.value;
        const oldValue = dropdown.dataset.currentValue;

        console.log('Type changed:', {roomId, oldValue, newType});

        // Update the dropdown styling immediately
        dropdown.classList.remove('type-lab', 'type-lecture');
        dropdown.classList.add(newType === 'Lab' ? 'type-lab' : 'type-lecture');

        // Get the room data to update
        fetch(getUrl)
            .then(response => response.json())
            .then(data => {
                const room = data.items[roomId];

                // Prepare update data
                const updateData = {
                    room_number: room.room_number,
                    type: newType,
                    availability: room.availability || 'Available'
                };

                console.log('Updating room type:', updateData);

                // Send update to backend
                fetch(`/update_item/${itemName}/${roomId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(updateData)
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Type update response:', data);
                    if (data.success) {
                        console.log('Type updated successfully!');
                        dropdown.dataset.currentValue = newType;
                    } else {
                        console.error('Failed to update type:', data.error);
                        alert('Failed to update type: ' + (data.error || 'Unknown error'));
                        // Revert dropdown to old value
                        dropdown.value = oldValue;
                        dropdown.classList.remove('type-lab', 'type-lecture');
                        dropdown.classList.add(oldValue === 'Lab' ? 'type-lab' : 'type-lecture');
                    }
                })
                .catch(error => {
                    console.error('Error updating type:', error);
                    alert('Error updating type');
                    // Revert dropdown to old value
                    dropdown.value = oldValue;
                    dropdown.classList.remove('type-lab', 'type-lecture');
                    dropdown.classList.add(oldValue === 'Lab' ? 'type-lab' : 'type-lecture');
                });
            })
            .catch(error => {
                console.error('Error fetching room data:', error);
            });
    }

    function handleAvailabilityChange(event) {
        const dropdown = event.target;
        const roomId = dropdown.dataset.roomId;
        const newAvailability = dropdown.value;
        const oldValue = dropdown.dataset.currentValue;

        console.log('Availability changed:', {roomId, oldValue, newAvailability});

        // Update the dropdown styling immediately
        dropdown.classList.remove('status-available', 'status-not-available');
        dropdown.classList.add(newAvailability === 'Not Available' ? 'status-not-available' : 'status-available');

        // Get the room data to update
        fetch(getUrl)
            .then(response => response.json())
            .then(data => {
                const room = data.items[roomId];

                // Prepare update data
                const updateData = {
                    room_number: room.room_number,
                    type: room.type,
                    availability: newAvailability
                };

                console.log('Updating room availability:', updateData);

                // Send update to backend
                fetch(`/update_item/${itemName}/${roomId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(updateData)
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Availability update response:', data);
                    if (data.success) {
                        console.log('Availability updated successfully!');
                        dropdown.dataset.currentValue = newAvailability;
                    } else {
                        console.error('Failed to update availability:', data.error);
                        alert('Failed to update availability: ' + (data.error || 'Unknown error'));
                        // Revert dropdown to old value
                        dropdown.value = oldValue;
                        dropdown.classList.remove('status-available', 'status-not-available');
                        dropdown.classList.add(oldValue === 'Not Available' ? 'status-not-available' : 'status-available');
                    }
                })
                .catch(error => {
                    console.error('Error updating availability:', error);
                    alert('Error updating availability');
                    // Revert dropdown to old value
                    dropdown.value = oldValue;
                    dropdown.classList.remove('status-available', 'status-not-available');
                    dropdown.classList.add(oldValue === 'Not Available' ? 'status-not-available' : 'status-available');
                });
            })
            .catch(error => {
                console.error('Error fetching room data:', error);
            });
    }

    function handleEdit(event) {
        const itemId = event.currentTarget.dataset.id;
        fetch(`/get_item/${itemName}/${itemId}`)
            .then(response => response.json())
            .then(item => {
                document.getElementById('editItemId').value = itemId;
                formFields.forEach(field => {
                    if (field.form_display) {
                        // Default value for availability if not set
                        let fieldValue = item[field.name] || '';
                        if (field.name === 'availability' && !item[field.name]) {
                            fieldValue = 'Available';
                        }

                        if (field.type === "select") {
                            const selectElement = document.getElementById(`edit_${field.name}`);
                            if (selectElement) {
                                selectElement.value = fieldValue;
                            }
                        } else {
                            const inputElement = document.getElementById(`edit_${field.name}`);
                            if (inputElement) {
                                inputElement.value = fieldValue;
                            }
                        }
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
        document.getElementById("addForm").reset();
    }

    editClose.onclick = function() {
        editModal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == addModal) {
            addModal.style.display = "none";
            document.getElementById("addForm").reset();
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

            // Disable submit button to prevent double-clicking
            const submitBtn = document.querySelector('#addForm button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Creating...';
            submitBtn.disabled = true;

            fetch(addUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                // Re-enable button
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;

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
                // Re-enable button on error
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;

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

        // Debug logging
        console.log('Updating room with data:', data);
        console.log('Item type:', itemName);
        console.log('Item ID:', itemId);

        fetch(`/update_item/${itemName}/${itemId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Update response:', data);
            if (data.success) {
                console.log('Update successful, refreshing table...');
                fetchItems();
                editModal.style.display = "none";
            } else {
                // Show error message
                console.error('Update failed:', data.error);
                alert("Error: " + (data.error || "Failed to update item"));
            }
        })
        .catch(error => {
            alert("Error: Failed to communicate with server");
            console.error('Error:', error);
        });
    }

    // Fetch items when the page loads
    fetchItems();

    // Bulk create functionality for rooms
    if (itemName === 'room' && MANAGEMENT_CONFIG.currentFloor) {
        const bulkCreateBtn = document.getElementById('bulkCreateBtn');
        const bulkModal = document.getElementById('bulkModal');
        const bulkClose = document.getElementById('bulkClose');
        const bulkCreateForm = document.getElementById('bulkCreateForm');
        const currentFloor = MANAGEMENT_CONFIG.currentFloor;

        if (bulkCreateBtn && bulkModal) {
            bulkCreateBtn.onclick = function() {
                bulkModal.style.display = 'block';
            };

            bulkClose.onclick = function() {
                bulkModal.style.display = 'none';
                bulkCreateForm.reset();
                document.getElementById('bulkErrorMessage').style.display = 'none';
            };

            window.onclick = function(event) {
                if (event.target == bulkModal) {
                    bulkModal.style.display = 'none';
                    bulkCreateForm.reset();
                    document.getElementById('bulkErrorMessage').style.display = 'none';
                }
            };

            bulkCreateForm.onsubmit = function(e) {
                e.preventDefault();

                // Use current floor number automatically
                const formData = {
                    floors: currentFloor.toString(),
                    rooms_per_floor: document.getElementById('rooms_per_floor').value,
                    type: document.getElementById('room_type').value
                };

                const errorMsg = document.getElementById('bulkErrorMessage');
                errorMsg.style.display = 'none';

                const submitBtn = bulkCreateForm.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Creating...';
                submitBtn.disabled = true;

                fetch('/bulk_create_rooms', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;

                    if (data.success) {
                        alert('✅ ' + data.message);
                        bulkModal.style.display = 'none';
                        bulkCreateForm.reset();
                        fetchItems();
                    } else {
                        errorMsg.textContent = data.error;
                        errorMsg.style.display = 'block';
                    }
                })
                .catch(error => {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                    errorMsg.textContent = 'Error creating rooms: ' + error.message;
                    errorMsg.style.display = 'block';
                });
            };
        }
    }

    // Special handling for course teacher lookup and section code
    if (itemName === 'course') {
        // Function to lookup teacher by registration number
        function setupTeacherLookup(prefix) {
            const regField = document.getElementById(`${prefix}teacher_registration`);
            const nameField = document.getElementById(`${prefix}teacher_name`);

            if (regField && nameField) {
                // Create error message div if it doesn't exist
                let errorDiv = regField.parentElement.querySelector('.teacher-error');
                if (!errorDiv) {
                    errorDiv = document.createElement('div');
                    errorDiv.className = 'teacher-error';
                    errorDiv.style.cssText = 'color: #ff6b6b; font-size: 0.85rem; margin-top: 5px; display: none;';
                    regField.parentElement.appendChild(errorDiv);
                }

                // Create success message div if it doesn't exist
                let successDiv = regField.parentElement.querySelector('.teacher-success');
                if (!successDiv) {
                    successDiv = document.createElement('div');
                    successDiv.className = 'teacher-success';
                    successDiv.style.cssText = 'color: #4caf50; font-size: 0.85rem; margin-top: 5px; display: none;';
                    regField.parentElement.appendChild(successDiv);
                }

                let debounceTimer;
                regField.addEventListener('input', function() {
                    clearTimeout(debounceTimer);
                    const regNumber = this.value.trim();

                    // Clear messages
                    errorDiv.style.display = 'none';
                    successDiv.style.display = 'none';
                    nameField.value = '';

                    if (!regNumber) return;

                    // Show loading state
                    nameField.value = 'Looking up...';

                    debounceTimer = setTimeout(() => {
                        fetch(`/lookup_teacher/${regNumber}`)
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    nameField.value = data.teacher.username;
                                    successDiv.textContent = `✓ Found: ${data.teacher.email}`;
                                    successDiv.style.display = 'block';
                                } else {
                                    nameField.value = '';
                                    errorDiv.textContent = '✗ ' + data.error;
                                    errorDiv.style.display = 'block';
                                }
                            })
                            .catch(error => {
                                nameField.value = '';
                                errorDiv.textContent = '✗ Error looking up teacher';
                                errorDiv.style.display = 'block';
                            });
                    }, 500); // Debounce for 500ms
                });
            }
        }

        // Setup teacher lookup for add form
        setupTeacherLookup('');


        // Function to update section code based on shift and digits
        function updateSectionCode(prefix) {
            const shift = document.getElementById(`${prefix}shift`);
            const digits = document.getElementById(`${prefix}section_digits`);
            const sectionCode = document.getElementById(`${prefix}section_code`);

            if (shift && digits && sectionCode) {
                const updateCode = () => {
                    const shiftValue = shift.value.toLowerCase().substring(0, 3); // "morning" -> "mor", "evening" -> "eve"
                    const digitsValue = digits.value;
                    if (shiftValue && digitsValue && digitsValue.length === 3) {
                        sectionCode.value = shiftValue + digitsValue;
                    }
                };

                shift.addEventListener('change', updateCode);
                digits.addEventListener('input', updateCode);
            }
        }

        // Function to parse section code into shift and digits when editing
        function parseSectionCode(prefix) {
            const sectionCode = document.getElementById(`${prefix}section_code`);
            const shift = document.getElementById(`${prefix}shift`);
            const digits = document.getElementById(`${prefix}section_digits`);

            if (sectionCode && shift && digits && sectionCode.value) {
                const code = sectionCode.value.toLowerCase();
                if (code.startsWith('mor')) {
                    shift.value = 'Morning';
                    digits.value = code.substring(3);
                } else if (code.startsWith('eve')) {
                    shift.value = 'Evening';
                    digits.value = code.substring(3);
                }
            }
        }

        // Setup for add form
        updateSectionCode('');

        // Override handleEdit to parse section code when editing
        const originalHandleEdit = handleEdit;
        handleEdit = function(event) {
            const itemId = event.currentTarget.dataset.id;
            fetch(`/get_item/${itemName}/${itemId}`)
                .then(response => response.json())
                .then(item => {
                    document.getElementById('editItemId').value = itemId;
                    formFields.forEach(field => {
                        if (field.name === "floor_number") {
                            document.getElementById(`edit_${field.name}`).value = item[field.name] || '';
                            document.getElementById(`edit_${field.name}`).readOnly = true;
                        } else if (field.type === "select") {
                            const selectElement = document.getElementById(`edit_${field.name}`);
                            if (selectElement) {
                                selectElement.value = item[field.name] || '';
                            }
                        } else {
                            document.getElementById(`edit_${field.name}`).value = item[field.name] || '';
                        }
                    });

                    // Parse section code after populating fields
                    parseSectionCode('edit_');

                    // Setup listeners for edit form
                    updateSectionCode('edit_');
                    setupTeacherLookup('edit_');

                    editModal.style.display = "block";
                });
        };

        // Re-attach edit event listeners with new handler
        document.querySelectorAll('.edit').forEach(button => {
            button.removeEventListener('click', originalHandleEdit);
            button.addEventListener('click', handleEdit);
        });
    }
});
