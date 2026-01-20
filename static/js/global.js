/*
Attach a "toggle" listener to each popup menu, to close the other menus
*/
var popupMenus = document.querySelectorAll(
	"nav#main-nav, ul, li, span.tei-bibl, span.tei-ref, span.tei-note, span.tei-seg,　details "
	);

for (var i=0; i < popupMenus.length; i = i + 1) {
	popupMenus.item(i).addEventListener(
		"click",
		function(event) {
            for (var j = 0; j < popupMenus.length; j = j + 1) {
                popupMenus.item(j).removeAttribute("data-open");
            }
            this.setAttribute("data-open", "true");
            event.stopPropagation();
        }
	);
}

/* mousing over a details summary should open the detail */
var summaries = document.querySelectorAll(
	"nav#main-nav, ul, li, span.tei-bibl > span.summary, span.tei-ref > span.summary, span.tei-note > span.summary, span.tei-seg > span.summary, details "
	);
for (var i=0; i < summaries.length; i = i + 1) {
	summaries.item(i).addEventListener(
        "click",
        function(event) {
            var menu = this.parentNode;
            var isOpen = menu.hasAttribute("data-open");

            for (var j = 0; j < popupMenus.length; j = j + 1) {
                popupMenus.item(j).removeAttribute("data-open");
            }

            if (!isOpen) {
                menu.setAttribute("data-open", "true");
            }

            event.stopPropagation();
        }
	);
}

/* mousing over any other part of the page should close the menus */
var body = document.querySelector("body");
body.addEventListener(
	"click",
	function(event) {
        for (var i = 0; i < popupMenus.length; i = i + 1) {
            popupMenus.item(i).removeAttribute("data-open");
        }
    }
);

/* keyboard */
var keys = document.querySelectorAll("button.key");
for (var i=0; i < keys.length; i = i + 1) {
	keys.item(i).addEventListener(
		"click",
		function(event) {
			var start = currentInputField.selectionStart;
			var end = currentInputField.selectionEnd;
			var text = currentInputField.value;
			var insertion = this.innerText;
			currentInputField.value = text.substring(0, start) + insertion + text.substring(end, text.length);
			currentInputField.setSelectionRange(start + insertion.length, start + insertion.length);
			currentInputField.focus();
			event.stopPropagation();
		}
	);
}
var currentInputField = document.querySelector("input[name=text]");
var inputFields = document.querySelectorAll("input[type=text]");
for (var i=0; i < inputFields.length; i = i + 1) {
	inputFields.item(i).addEventListener(
		"focus",
		function(event) {
			currentInputField = this;
			console.log(currentInputField);
		}
	);
}

/* parallel passages highlighting */
const passages = document.getElementsByClassName("type-parallel")

for (const passage of passages) {
	if (passage.classList.contains("tei-seg")) {
		passage.addEventListener("mouseover", function(e) {
			let idToCompare = e.target.id.slice(1)
			for (const p of passages) {
				if (p.tagName === "SPAN" && p.hasAttribute("id")) {
					const id = p.getAttribute("id")
					if (idToCompare === id.split("g")[1]) {
						p.style.backgroundColor = "yellow"
					}
				}
			}
		}
		)
	}
}
for (const passage of passages) {
	passage.addEventListener("mouseout", function() {
		for (const p of passages) {
			p.style.backgroundColor = "transparent"
		}
	}
	)
}
