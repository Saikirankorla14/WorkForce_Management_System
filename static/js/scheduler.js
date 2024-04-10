$("#worker-select").change(function() {
    var workerId = $(this).val();

    $.ajax({
        url: "/get_worker_details/",  // URL to your Django view
        method: "GET",
        data: { worker_id: workerId },
        success: function(response) {
            // Update the DOM with the received worker details
            $("#worker-details").html(response);
        },
        error: function(xhr, status, error) {
            console.error(xhr.responseText);
        }
    });
});
