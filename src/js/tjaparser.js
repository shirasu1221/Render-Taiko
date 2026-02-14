class TjaParser {
	constructor(content, tjaFile, allFiles) {
		this.content = content;
		this.tjaFile = tjaFile;
		this.allFiles = allFiles;
		this.lines = content.split(/\r?\n/);
		this.header = {};
		this.courses = {};
		this.parse();
	}

	parse() {
		let currentCourse = null;
		let currentData = [];

		for (let line of this.lines) {
			line = line.trim();
			if (!line || line.startsWith("//")) continue;

			if (line.startsWith("#START")) {
				currentData = [];
			} else if (line.startsWith("#END")) {
				if (currentCourse) {
					currentCourse.data = currentData.join("");
				}
			} else if (line.includes(":")) {
				let [key, value] = line.split(":").map(s => s.trim());
				key = key.toUpperCase();

				if (key === "COURSE") {
					let difficulty = value.toLowerCase();
					currentCourse = {
						difficulty: difficulty,
						data: ""
					};
					this.courses[difficulty] = currentCourse;
				} else if (!currentCourse) {
					this.header[key] = value;
				}
			} else if (currentCourse) {
				currentData.push(line);
			}
		}

		// メタデータの整理
		this.title = this.header["TITLE"] || this.tjaFile.name.replace(".tja", "");
		this.subtitle = this.header["SUBTITLE"] || "";
		this.audio = this.header["WAVE"];
		
		// 音源ファイルの紐付け
		if (this.audio && this.allFiles) {
			for (let file of this.allFiles) {
				if (file.name.toLowerCase() === this.audio.toLowerCase()) {
					this.audioFile = file;
					break;
				}
			}
		}
	}
}
