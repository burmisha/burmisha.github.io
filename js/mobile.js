findSet = function(hid) {
	for (var j = 0; j < allPhotos.length; j++) {
		if (hid.localeCompare(allPhotos[j].id) == 0){
			return j;
		}
	};
	alert("none for " + hid);
};

addPhotoset = function(photoset) {
	var id = "div#" + photoset.id;
	$(id).append('<h2>' + photoset.title + '</h2>');
	var filenames = "", cl = "";
	if (photoset.size == 1) {
		filenames = photoset.filenames;
		cl = "bigphoto";
	} else {
		filenames = photoset.filenames_small;
		cl = "smallphoto";
	};
	for (var i = 0; i < filenames.length; i++) {
		var newdiv = '<div style="background-image:url('+ filenames[i] + ')" id="' + photoset.id + "_" + ('000'+i).slice(-3) +'"></div>';
		$(id).append(newdiv);
	};
	$(id + " div").addClass(cl);
	$(id).append('<p class="description">' + photoset.text + '</p>');
}

$(function(){
	$("#links").click(function(){
		$("#content").load("links.html");
	});

	$("#bio").click(function(){
		$("#content").load("bio.html");
	});

	$("#main").click(function(){
		$("#content").load("main.html");
	});

	$("#photo").click(function(){
		$("#content").empty();
		for (var j = 0; j < allPhotos.length; j++) {
			var photoset = allPhotos[j];
			$("#content").append('<div class="photoset" id="'+ photoset.id + '"></div>');
			addPhotoset(photoset);
			$("#" + photoset.id).on('click', 'div', function(event){
				var id = $(this).attr("id");
				var photoset = allPhotos[findSet((id).slice(0,-4))];
				var number = parseInt(id.slice(-4), 10)
				$("#" + photoset.id).empty();
				photoset.size = 1 - photoset.size;
				addPhotoset(photoset); 
				$("html, body").animate({scrollTop: $('#' + id).position().top}, 800);
				event.stopImmediatePropagation()
			});
		};
	});
})
