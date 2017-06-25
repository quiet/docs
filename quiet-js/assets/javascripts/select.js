(function(){
    var select = document.querySelector("select");
    select.onchange = function(ev){
        window.location = this.options[this.selectedIndex].dataset.url + window.location.hash;
    };
})();
