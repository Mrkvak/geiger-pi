var isLoaded = false;
var error = false;
var cpmData = undefined;

async function getData() {
	await fetch("/cgi-bin/getcpm.cgi")
		.then(res => res.json())
		.then(
			(result) => {
				isLoaded = true;
				cpmData = result;
				error = undefined;
			},
			(commError) => {
				isLoaded = true;
				cpmData = undefined;
				error = commError;
			}
		);


	if (error) {
		setData("Error fetching data.");
	}

	if (!isLoaded) {
		setData("Loading...");
	}

	if (cpmData.avgCPM1min < 250) {
		bgColor = "white";
	} else if (cpmData.avgCPM1min < 500) {
		bgColor = "orange";
	} else {
		bgColor = "red";
	}
	setData("CPM: "+cpmData.avgCPM1min+", last second CPS: "+cpmData.currentCPS+"; Last updated: "+cpmData.lastUpdate);
	document.getElementById("rtdata").style.backgroundColor=bgColor;
}


function setData(data) {
	document.getElementById("rtdata").innerHTML = data;
	setTimeout(getData, 700);
}


function reloadImages() {
	var imgs = document.getElementsByClassName("autorefresh");
	var i;

	for (i = 0; i < imgs.length; i++) {
		var src = imgs[i].src;
		src.replace(/\?ts=[0-9]*/g, "");
		imgs[i].src=src+"?ts="+Date.now();
	}
	setTimeout(reloadImages, 45000);
}


window.onload = function() {
	getData();
	setTimeout(reloadImages, 45000);
}

