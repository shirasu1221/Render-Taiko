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
		
		this.linkGdriveFolder = document.createElement("div")
		this.linkGdriveFolder.classList.add("custom-songs-item")
		
		// Googleドライブ機能の無効化（エラー回避）
		if (false){
			this.setAltText(this.linkGdriveFolder, strings.customSongs.gdriveFolder)
			pageEvents.add(this.linkGdriveFolder, ["mousedown", "touchstart"], this.gdriveFolder.bind(this))
			this.items.push(this.linkGdriveFolder)
			if(this.selected === -1){
				this.linkGdriveFolder.classList.add("selected")
				this.selected = this.items.length - 1
			}
		}
		
		this.linkLocalFolder = document.createElement("div")
		this.linkLocalFolder.classList.add("custom-songs-item")
		this.setAltText(this.linkLocalFolder, strings.customSongs.localFolder)
		pageEvents.add(this.linkLocalFolder, ["mousedown", "touchstart"], this.localFolder.bind(this))
		this.items.push(this.linkLocalFolder)
		if(this.selected === -1){
			this.linkLocalFolder.classList.add("selected")
			this.selected = this.items.length - 1
		}
		
		this.view.appendChild(this.linkLocalFolder)
		
		this.pressedKeys = {}
		this.keyboard = new Keyboard({
			confirm: ["enter", "space", "don_l", "don_r"],
			back: ["escape"],
			left: ["left", "ka_l"],
			right: ["right", "ka_r"],
			up: ["up"],
			down: ["down"]
		}, this.keyPress.bind(this))
		this.gamepad = new Gamepad({
			confirm: ["b", "start", "ls", "rs"],
			back: ["a"],
			left: ["l", "lsl", "lt"],
			right: ["r", "lsr", "rt"],
			up: ["u", "lsu"],
			down: ["d", "lsd"]
		}, this.keyPress.bind(this))
	}
	
	setAltText(element, text){
		element.innerText = text
		element.setAttribute("alt", text)
	}
	
	keyPress(pressed, name){
		if(!pressed){
			return
		}
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
			var files = e.target.files
			if(files.length > 0){
				this.loadFiles(files)
			}
		}
		input.click()
	}
	
	gdriveFolder(){
		// 無効化済みのため空
	}
	
	loadFiles(files){
		var tjaFiles = []
		for(var i = 0; i < files.length; i++){
			if(files[i].name.toLowerCase().endsWith(".tja")){
				tjaFiles.push(files[i])
			}
		}
		
		if(tjaFiles.length === 0){
			alert(strings.customSongs.noTjaFiles)
			return
		}
		
		this.songs = []
		this.loadedCount = 0
		
		tjaFiles.forEach(file => {
			var reader = new FileReader()
			// 【重要】文字化け対策：まずUTF-8で読み込み
			reader.onload = (e) => {
				var result = e.target.result
				// 文字化け特有の記号（）をチェック
				if (result.includes('') || /[\uFFFD]/.test(result)) {
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
	
	addSong(content, tjaFile, allFiles){
		var song = new TjaParser(content, tjaFile, allFiles)
		if(song.unloaded){
			this.loadedCount++
		}else{
			this.songs.push(song)
			this.loadedCount++
		}
		
		if(this.loadedCount === this.songs.length + (this.songs.unloaded || 0)){
			this.songsLoaded()
		}
	}
	
	songsLoaded(){
		if(this.songs.length === 0){
			alert(strings.customSongs.noTjaFiles)
			return
		}
		
		assets.customSongs = this.songs
		this.clean()
		new SongSelect("customSongs", false, this.touchEnabled)
	}

	clean(){
		this.keyboard.clean()
		this.gamepad.clean()
		this.view.classList.add("view-hidden")
		this.view.innerHTML = ""
		// songSelectが存在する場合のみcleanを呼ぶ安全策
		if (this.songSelect && this.songSelect.clean) {
			this.songSelect.clean()
		}
	}
}
