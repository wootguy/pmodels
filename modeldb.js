
var model_data = {};
var model_names;
var can_load_new_model = false;
var model_load_queue;
var model_unload_waiting;
var hlms_is_ready = false;

var model_results; // subset of model_names
var results_per_page = 40;
//var result_offset = 0;
var result_offset = 1201;
var data_repo_count = 16;

function fetchJSONFile(path, callback) {
	var httpRequest = new XMLHttpRequest();
	httpRequest.onreadystatechange = function() {
		if (httpRequest.readyState === 4 && httpRequest.status === 200 && callback) {
			var data = JSON.parse(httpRequest.responseText);
			callback(data);
		}
	};
	httpRequest.open('GET', path);
	httpRequest.send(); 
}

function stopDownloads() {
	if (!hlms_is_ready) {
		console.log("Can't cancel yet");
		return; // don't want to cancel this accidentally
	}
	
	if (window.stop !== undefined) {
		window.stop();
	}
	else if (document.execCommand !== undefined) {
		document.execCommand("Stop", false);
	}   
}

function hlms_load_model(model_name, t_model, seq_groups) {
	var repo_url = get_repo_url(model_name);
	var model_path = repo_url + "models/player/" + model_name + "/";
	
	if (can_load_new_model) {
		Module.ccall('load_new_model', null, ['string', 'string', 'string', 'number'], [model_path, model_name, t_model, seq_groups], {async: true});
		can_load_new_model = false;
		return true;
	} else {
		console.log("Can't load a new model yet. Waiting for previous model to load.");
		model_load_queue = model_name;
		
		popup.getElementsByClassName("loader")[0].style.visibility = "hidden";
		popup.getElementsByClassName("loader-text")[0].textContent = "Failed to load. Try refreshing.";
		
		return false;
	}
}

function view_model(model_name) {
	var model_path = "models/player/" + model_name + "/";
	var popup = document.getElementById("model-popup");
	var popup_bg = document.getElementById("model-popup-bg");
	var img = popup.getElementsByTagName("img")[0];
	var canvas = popup.getElementsByTagName("canvas")[0];
	var repo_url = get_repo_url(model_name);
	popup.style.display = "block";
	popup_bg.style.display = "block";
	canvas.style.visibility = "hidden";
	img.style.display = "block";
	img.setAttribute("src", "");
	img.setAttribute("src", repo_url + model_path + model_name + "_small.png");
	
	popup.getElementsByClassName("details-header")[0].textContent = model_name;
	popup.getElementsByClassName("polycount")[0].textContent = "???";
	popup.getElementsByClassName("loader")[0].style.visibility = "visible";
	popup.getElementsByClassName("loader-text")[0].style.visibility = "visible";
	popup.getElementsByClassName("loader-text")[0].textContent = "Loading (0%)";
	
	img.onload = function() {
		img.setAttribute("src", repo_url + model_path + model_name + "_large.png");
		
		img.onload = function() {
			img.onload = undefined;
		};
	}
	
	fetchJSONFile(repo_url + model_path + model_name + ".json", function(data) {
		let num = parseInt(data["tri_count"]);
		popup.getElementsByClassName("polycount")[0].textContent = num.toLocaleString(undefined);
		
		hlms_load_model(model_name, data["t_model"] || "", data["seq_groups"]);
	});
}

function close_model_viewer() {
	var popup = document.getElementById("model-popup");
	var popup_bg = document.getElementById("model-popup-bg");
	popup.style.display = "none";
	popup_bg.style.display = "none";
	
	if (can_load_new_model) {
		Module.ccall('unload_model', null, [], [], {async: true});
	} else {
		model_unload_waiting = true;
	}
}

function hlms_do_queued_action() {
	if (model_load_queue) {
		if (hlms_load_model(model_load_queue)) {
			model_load_queue = undefined;
			model_unload_waiting = false;
		}
	} else if (model_unload_waiting) {
		Module.ccall('unload_model', null, [], [], {async: true});
		model_unload_waiting = false;
	}
}

function hlms_model_load_complete(successful) {
	if (successful) {
		var popup = document.getElementById("model-popup");
		var img = popup.getElementsByTagName("img")[0];
		var canvas = popup.getElementsByTagName("canvas")[0];
		
		canvas.style.visibility = "visible";
		img.style.display = "none";
		img.setAttribute("src", "");
		
		popup.getElementsByClassName("loader")[0].style.visibility = "hidden";
		popup.getElementsByClassName("loader-text")[0].style.visibility = "hidden";
		
		console.log("Model loading finished");
	} else {
		console.log("Model loading failed");
	}
	
	can_load_new_model = true;
	setTimeout(function() {
		hlms_do_queued_action();
	}, 100);
}

function hlms_ready() {
	can_load_new_model = true;
	hlms_is_ready = true;
	console.log("Model viewer is ready");
	hlms_do_queued_action();
	
	// GLFW will disable backspace and enter otherwise (WTF?)
	window.removeEventListener("keydown", GLFW.onKeydown, true);
	window.addEventListener("keydown", function() {
		GLFW.onKeyChanged(event.keyCode, 1); // GLFW_PRESS or GLFW_REPEAT
	}, true);
}

function load_page() {
	stopDownloads();
	
	document.getElementsByClassName("result-total")[0].textContent = "" + model_results.length;
	document.getElementsByClassName("page-start")[0].textContent = "" + (result_offset+1);
	document.getElementsByClassName("page-end")[0].textContent = "" + Math.min(result_offset+results_per_page, model_results.length);
	
	update_model_grid();
}

function next_page() {
	result_offset += results_per_page;
	if (result_offset >= model_results.length) {
		result_offset -= results_per_page;
		return;
	}
	load_page();
}

function prev_page() {
	result_offset -= results_per_page;
	if (result_offset < 0) {
		result_offset = 0;
	}
	load_page();
}

function first_page() {
	result_offset = 0;
	load_page();
}

function last_page() {
	result_offset = 0;
	while (true) {
		result_offset += results_per_page;
		if (result_offset >= model_results.length) {
			result_offset -= results_per_page;
			break;
		}
	}
	load_page();
}

function load_results() {
	first_page();
}

function apply_filters() {
	var name_filter = document.getElementById("name-filter").value;
	
	if (name_filter.length > 0) {
		name_parts = name_filter.toLowerCase().split(" ");
		console.log("FILTER: " + name_filter);
		
		model_results = [];
		for (var i = 0; i < model_names.length; i++) {
			for (var k = 0; k < name_parts.length; k++) {
				if (model_names[i].toLowerCase().includes(name_parts[k])) {
					model_results.push(model_names[i]);
				}
			}
		}
	}
	else
		model_results = model_names;
	
	load_results();
}

function update_model_grid() {
	var total_models = model_names.length;
	var grid = document.getElementById("model-grid");
	var cell_template = document.getElementById("model-cell-template");
	
	grid.innerHTML = "";
	
	var total_cells = 0;
	var idx = 0;
	model_results.every(function(model_name) {
		//console.log("Loading model: " + model_name);
		
		idx += 1;
		if (idx < result_offset) {
			return true;
		}
		
		var cell = cell_template.cloneNode(true);
		var img = cell.getElementsByTagName("img")[0];
		var name = cell.getElementsByClassName("name")[0];
		var repo_url = get_repo_url(model_name);
		cell.setAttribute("class", "model-cell");
		cell.removeAttribute("id");
		img.setAttribute("src", repo_url + "models/player/" + model_name + "/" + model_name + "_small.png");
		img.addEventListener("click", function() {view_model(model_name);} );
		name.innerHTML = model_name;
		name.setAttribute("title", model_name);
		//name.addEventListener("click", function(event) { console.log("SELECT ALL! ", event.target); event.target.select(); } );
		grid.appendChild(cell);
		
		total_cells += 1;
		return total_cells < results_per_page;
	});
}

function get_repo_url(model_name) {
	var repoId = hash_code(model_name) % data_repo_count;
	
	return "https://wootguy.github.io/scmodels_data_" + repoId + "/";
}

function hash_code(str) {
	var hash = 0;

	for (var i = 0; i < str.length; i++) {
		var char = str.charCodeAt(i);
		hash = ((hash<<5)-hash)+char;
		hash = hash % 15485863; // prevent hash ever increasing beyond 31 bits

	}
	return hash;
}

document.addEventListener("DOMContentLoaded",function() {
	fetchJSONFile("models.json", function(data) {
		model_data = data;
		model_names = Object.keys(model_data);
		model_names.sort();
		model_results = model_names;
		
		apply_filters();
	});
	
	document.getElementById("model-popup-bg").addEventListener("click", close_model_viewer);
	document.getElementsByClassName("page-next-container")[0].addEventListener("click", next_page);
	document.getElementsByClassName("page-prev-container")[0].addEventListener("click", prev_page);
	document.getElementsByClassName("page-first-container")[0].addEventListener("click", first_page);
	document.getElementsByClassName("page-last-container")[0].addEventListener("click", last_page);
	document.getElementById("name-filter").addEventListener("keyup", apply_filters);
});
