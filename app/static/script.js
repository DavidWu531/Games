function toggle_div() {
    // Toggle visiblity of respective platform system requirements field
    const pc = document.querySelector('input[name="platforms"][value="1"]');
    const ps = document.querySelector('input[name="platforms"][value="2"]');
    const xb = document.querySelector('input[name="platforms"][value="3"]');
    
    document.getElementById("pc_requirements").style.display = pc && pc.checked ? "block" : "none";
    document.getElementById("ps_requirements").style.display = ps && ps.checked ? "block" : "none";
    document.getElementById("xb_requirements").style.display = xb && xb.checked ? "block" : "none";
}
document.addEventListener("DOMContentLoaded", toggle_div);

function delete_account() {
    // Warning message asking for confirmation of account deletion
    if (confirm("Are you sure you want to delete your account? This action cannot be undone!")) {
        window.location.href = "/delete";
    }
}

function delete_game(id) {
    // Warning message asking for confirmation of game deletion
    if (confirm("Are you sure you want to delete this game? This action cannot be undone!")) {
        window.location.href = "/admin/game/delete/${id}";
    }
}