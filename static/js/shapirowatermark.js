const {
  createApp,
  ref
} = Vue
const {
  createVuetify
} = Vuetify
const vuetify = createVuetify()
//vue3-sfc-loader config
const options = {
    moduleCache: {
        vue: Vue
    },
    //read subdirectory vue component file.
    async getFile(url) {
        const res = await fetch(url);
        if ( !res.ok )
        throw Object.assign(new Error(res.statusText + ' ' + url), { res });
        return {
        getContentData: asBinary => asBinary ? res.arrayBuffer() : res.text(),
        }
    },
    addStyle(textContent) {
        const style = Object.assign(document.createElement('style'), { textContent });
        const ref = document.head.getElementsByTagName('style')[0] || null;
        document.head.insertBefore(style, ref);
    },
}
const { loadModule } = window["vue3-sfc-loader"];

createApp({
  setup() {
  },
  components: {
    "shapirowatermark": Vue.defineAsyncComponent(() => loadModule("/js/vue-component/shapirowatermark.vue", options))
  },
}).use(vuetify).mount('#app')
