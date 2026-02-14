class CustomSongs {
	constructor(...args) {
		this.init(...args)
	}

	init(songSelect) {
		this.songSelect = songSelect || {}
		this.touchEnabled = (songSelect && songSelect.touchEnabled) || false

		loader.changePage("customsongs", false)

		this.view = document.getElementById("custom-songs")
		this.view.classList.remove("view-hidden")

		this.items = []
		this.linkLocalFolder = document.createElement("div")
		this.linkLocalFolder.classList.add("custom-songs-item")
		this.setAltText(this.linkLocalFolder, strings.customSongs.localFolder)
		pageEvents.add(this.linkLocalFolder, ["mousedown", "touchstart"], this.localFolder.bind(this))
		this.items.push(this.linkLocalFolder)

		this.selected = 0
		this.linkLocalFolder.classList.add("selected")
		this.view.appendChild(this.linkLocalFolder)

		this.keyboard = new Keyboard({
			confirm: ["enter", "space", "don_l", "don_r"],
			back: ["escape"]
		}, this.keyPress.bind(this))
		this.gamepad = new Gamepad({
			confirm: ["b", "start"],
			back: ["a"]
		}, this.keyPress.bind(this))
	}

	setAltText(element, text) {
		element.innerText = text
		element.setAttribute("alt", text)
	}

	keyPress(pressed, name) {
		if (!pressed) return
		if (name === "back") {
			this.clean()
			new SongSelect("customSongs", false, this.touchEnabled)
		}
	}

	localFolder() {
		var input = document.createElement("input")
		input.type = "file"
		input.webkitdirectory = true
		input.onchange = (e) => {
			if (e.target.files.length > 0) this.loadFiles(e.target.files)
		}
		input.click()
	}

	loadFiles(files) {
		var tjaFiles = []
		for (var i = 0; i < files.length; i++) {
			if (files[i].name.toLowerCase().endsWith(".tja")) {
				tjaFiles.push(files[i])
			}
		}

		if (tjaFiles.length === 0) {
			alert(strings.customSongs.noTjaFiles)
			return
		}

		this.songs = []
		this.totalTja = tjaFiles.length
		this.loadedCount = 0

		tjaFiles.forEach(file => {
			var reader = new FileReader()
			reader.onload = (e) => {
				var result = e.target.result
				if (result.includes('\uFFFD')) {
					var sjisReader = new FileReader()
					sjisReader.onload = (sjisE) => {
						this.addSong(sjisE.target.result, file, files)
					}
					sjisReader.readAsText(file, "Shift-JIS")
				} else {
					this.addSong(result, file, files)
				}
			}
			reader.readAsText(file, "UTF-8")
		})
	}

	addSong(content, tjaFile, allFiles) {
		try {
			var song = new TjaParser(content, tjaFile, allFiles)
			if (!song.unloaded) {
				this.songs.push(song)
			}
		} catch (e) {
			console.error("TJA Parse Error:", e)
		}

		this.loadedCount++
		// 全てのTJAファイルの読み込み試行が終わったら次へ
		if (this.loadedCount >= this.totalTja) {
			this.songsLoaded()
		}
	}

	songsLoaded() {
		if (this.songs.length > 0) {
			assets.customSongs = this.songs
			this.clean()
			// 選曲画面の初期化を少し遅らせて確実に描画させる
			setTimeout(() => {
				new SongSelect("customSongs", false, this.touchEnabled)
			}, 200)
		} else {
			alert(strings.customSongs.noTjaFiles)
		}
	}

	clean() {
		if (this.keyboard) this.keyboard.clean()
		if (this.gamepad) this.gamepad.clean()
		if (this.view) {
			this.view.classList.add("view-hidden")
			this.view.innerHTML = ""
		}
		if (this.songSelect && this.songSelect.clean) {
			this.songSelect.clean()
		}
	}
}
