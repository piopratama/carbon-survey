// js/project_state.js

function getCurrentProject() {
  return localStorage.getItem("current_project_id");
}

function setCurrentProject(id) {
  localStorage.setItem("current_project_id", id);
}

function clearCurrentProject() {
  localStorage.removeItem("current_project_id");
}
