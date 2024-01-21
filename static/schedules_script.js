     src="https://code.jquery.com/jquery-3.6.4.min.js">

    // Function to toggle the visibility of columns for day 6 and day 7
    function toggleLongWeek() {
        // Get the checkbox element
        var checkbox = document.getElementById('showLongWeek');

        // Get the table cells for day 6 and day 7
        var cellsDay6 = document.querySelectorAll('td[data-day="2024-01-06"]');
        var cellsDay7 = document.querySelectorAll('td[data-day="2024-01-07"]');

        var cellsDay6Th = document.querySelectorAll('th[data-day="2024-01-06"]');
        var cellsDay7Th = document.querySelectorAll('th[data-day="2024-01-07"]');

        // Toggle the visibility based on the checkbox state
        if (checkbox.checked) {
            cellsDay6.forEach(function (cell) {
                cell.style.display = 'table-cell';
            });
            cellsDay7.forEach(function (cell) {
                cell.style.display = 'table-cell';
            });
            cellsDay6Th.forEach(function (cell) {
                cell.style.display = 'table-cell';
            });
            cellsDay7Th.forEach(function (cell) {
                cell.style.display = 'table-cell';
            });
        } else {
            cellsDay6.forEach(function (cell) {
                cell.style.display = 'none';
            });
            cellsDay7.forEach(function (cell) {
                cell.style.display = 'none';
            });
            cellsDay6Th.forEach(function (cell) {
                cell.style.display = 'none';
            });
            cellsDay7Th.forEach(function (cell) {
                cell.style.display = 'none';
            });
        }
    }

    // Function to toggle the visibility of week lists
    function addDropdown(button) {
        var position = $(button).closest('td').data('position');
        var day = $(button).closest('td').data('day');

        // Get the existing dropdown in the same cell
        var existingDropdown = $(button).closest('td').find('.worker-dropdown').first();

        // Clone the existing dropdown and remove the selected attribute
        var newDropdown = existingDropdown.clone().removeAttr('selected');

        // Append the new dropdown to the parent td
        $(button).before(newDropdown);
    }

    // Function to remove the last dropdown
    function removeDropdown(button) {
        var dropdowns = $(button).closest('td').find('.worker-dropdown');

        // Ensure there is at least one dropdown before removing
        if (dropdowns.length > 1) {
            dropdowns.last().remove();
        }
    }

    // Ensure the DOM is ready before attaching event handlers
    $(document).ready(function () {
        toggleLongWeek();
        // Prevent the default form submission to handle it using AJAX
        $("#scheduleForm").submit(function (e) {
            e.preventDefault();
            saveSchedule();
        });

        // Function to handle saving the schedule using AJAX
        function saveSchedule() {
            var scheduleData = {};

            // Iterate through each dropdown to get the selected worker for each position and day
            $(".worker-dropdown").each(function () {
                var position = $(this).data("position");
                var day = $(this).data("day");
                var worker = $(this).val();

                // Initialize the position in the scheduleData object if not present
                if (!scheduleData[day]) {
                    scheduleData[day] = {};
                }

                // Assign the selected worker for the position and day
                scheduleData[day][position] = worker;
            });

            // Use AJAX to send the schedule data to the server
            $.ajax({
                type: "POST",
                url: "/save_schedule",
                contentType: "application/json;charset=UTF-8",
                data: JSON.stringify(scheduleData),
                success: function (response) {
                    // Handle success (if needed)
                    console.log("Schedule saved successfully!");
                },
                error: function (error) {
                    // Handle error (if needed)
                    console.error("Error saving schedule:", error);
                }
            });
        }
    });

