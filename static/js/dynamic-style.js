const passages = document.getElementsByClassName("type-parallel")

for (const passage of passages) {
	if (passage.tagName === "DETAILS") {
		passage.addEventListener("mouseover", function(e) {
			let idToCompare = e.target.id.slice(1)
			for (const p of passages) {
				if (p.tagName === "SPAN") {
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