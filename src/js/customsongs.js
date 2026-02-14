class CustomSongs{
	constructor(...args){
		this.init(...args)
	}
	init(songSelect){
		this.songSelect = songSelect
		this.touchEnabled = songSelect.touchEnabled
		loader.changePage("customsongs", false)
		
		this.view = document.getElementById("custom-songs")
		this.view.classList.remove("view-hidden")
		
		this.items = []
		this.selected = -1
		
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
	
	setAltText(element, text){
		element.innerText = text
		element.setAttribute("alt", text)
	}
	
	keyPress(pressed, name){
		if(!pressed) return
		if(name === "back"){
			this.clean()
			new SongSelect("customSongs", false, this.touchEnabled)
		}
	}
	
	localFolder(){
		var input = document.createElement("input")
		input.type = "file"
		input.webkitdirectory = true
		input.onchange = (e) => {
			if(e.target.files.length > 0) this.loadFiles(e.target.files)
		}
		input.click()
	}
	
	loadFiles(files){
		var tjaFiles = []
		for(var i = 0; i < files.length; i++){
			if(files[i].name.toLowerCase().endsWith(".tja")) tjaFiles.push(files[i])
		}
		if(tjaFiles.length === 0){
			alert(strings.customSongs.noTjaFiles)
			return
		}
		this.songs = []
		this.loadedCount = 0
		tjaFiles.forEach(file => {
			var reader = new FileReader()
			reader.onload = (e) => {
				var result = e.target.result
				if (result.includes('') || /[\uFFFD]/.test(result)) {
					var sjisReader = new FileReader()
					sjisReader.onload = (sjisE) => this.addSong(sjisE.target.result, file, files)
					sjisReader.readAsText(file, "Shift-JIS")
				} else {
					this.addSong(result, file, files)
				}
			}
			reader.readAsText(file, "UTF-8")
		})
	}
	
	addSong(content, tjaFile, allFiles){
		var song = new TjaParser(content, tjaFile, allFiles)
		this.loadedCount++
		if(!song.unloaded) this.songs.push(song)
		if(this.loadedCount === this.loadedCount){ // 全ファイル走査完了チェック
			// 一定時間待ってから遷移（パース待ち）
			setTimeout(() => this.songsLoaded(), 100)
		}
	}
	
	songsLoaded(){
		if(this.songs.length > 0){
			assets.customSongs = this.songs
			this.clean()
			new SongSelect("customSongs", false, this.touchEnabled)
		}
	}

	clean(){
		if(this.keyboard) this.keyboard.clean()
		if(this.gamepad) this.gamepad.clean()
		this.view.classList.add("view-hidden")
		this.view.innerHTML = ""
		if (this.songSelect && this.songSelect.clean) this.songSelect.clean()
	}
}
