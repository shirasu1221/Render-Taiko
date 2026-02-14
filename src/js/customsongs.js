class CustomSongs {
    constructor(songSelect) {
        this.songSelect = songSelect;
        this.view = document.getElementById("custom-songs");
        this.init();
    }
    init() {
        this.view.classList.remove("view-hidden");
        this.view.innerHTML = '<div class="custom-songs-item selected" id="load-folder">フォルダを選択</div>';
        document.getElementById("load-folder").onclick = () => this.localFolder();
    }
    localFolder() {
        let input = document.createElement("input");
        input.type = "file";
        input.webkitdirectory = true;
        input.onchange = (e) => this.loadFiles(e.target.files);
        input.click();
    }
    loadFiles(files) {
        let tjaFiles = Array.from(files).filter(f => f.name.toLowerCase().endsWith(".tja"));
        this.songs = [];
        let loaded = 0;
        tjaFiles.forEach(file => {
            let reader = new FileReader();
            reader.onload = (e) => {
                let content = e.target.result;
                if (content.includes('\uFFFD')) {
                    let sjisReader = new FileReader();
                    sjisReader.onload = (se) => this.addSong(se.target.result, file, files, ++loaded === tjaFiles.length);
                    sjisReader.readAsText(file, "Shift-JIS");
                } else {
                    this.addSong(content, file, files, ++loaded === tjaFiles.length);
                }
            };
            reader.readAsText(file, "UTF-8");
        });
    }
    addSong(c, f, af, last) {
        let s = new TjaParser(c, f, af);
        if (!s.unloaded) this.songs.push(s);
        if (last) {
            assets.customSongs = this.songs;
            this.view.classList.add("view-hidden");
            new SongSelect("customSongs", false, false);
        }
    }
}
