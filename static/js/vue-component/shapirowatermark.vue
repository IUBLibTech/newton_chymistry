<template>
<v-container>
    <v-row justify="space-between">
        <v-col cols="7">
            <v-menu :close-on-content-click="false">
                <template v-slot:activator="{ props: activatorProps }">
                    <v-btn
                        v-bind="activatorProps" prepend-icon="mdi-filter-menu" text="Filter"
                        size="x-large" rounded="xl" :color="chymistryPrimaryColor">
                    </v-btn>
                </template>
                <v-card elevated width="900" min-height="250">
                    <v-row justify="center" class="mt-8">
                        <v-col cols="5">
                            <v-row>
                                <div class="text-h5">Time Range</div>
                            </v-row>
                            <v-row class="mt-10">
                                <v-range-slider
                                    :color="chymistryPrimaryColor"
                                    :thumb-color="chymistryPrimaryColor"
                                    v-model="duration"
                                    @update:modelValue="setMaxMinHeight"
                                    :step="1"
                                    thumb-label="always"
                                    :min="baseMinYear"
                                    :max="baseMaxYear"
                                />
                            </v-row>
                        </v-col>
                        <v-col cols="5">
                            <v-row>
                                <div class="text-h5">Timeline Height(px)</div>
                            </v-row>
                            <v-row class="mt-10">
                                <v-slider
                                    :color="chymistryPrimaryColor"
                                    :thumb-color="chymistryPrimaryColor"
                                    v-model="height"
                                    @update:modelValue="refreshCanvas"
                                    :step="sliderStep"
                                    thumb-label="always"
                                    :min="minHeight"
                                    :max="maxHeight"
                                />
                            </v-row>
                        </v-col>
                    </v-row>
                    <v-row justify="center" class="pa-1">
                        <v-col cols="1">
                            <v-row class="pa-2">
                                <v-btn
                                    class="ml-n8"
                                    rounded="xl"
                                    min-width="100"
                                    :color="chymistryPrimaryColor"
                                    @click="selectAllFilteringKeywords"
                                >
                                Select<br/>All
                                </v-btn>
                            </v-row>
                            <v-row class="pa-2">
                                <v-btn
                                    class="ml-n8"
                                    rounded="xl"
                                    min-width="100"
                                    :color="chymistryPrimaryColor"
                                    @click="unselectAllFilteringKeywords"
                                >
                                Unselect<br/>All
                                </v-btn>
                            </v-row>
                        </v-col>
                        <v-col cols="4">
                        <v-select
                            v-model="largerCategoriesChosen"
                            :items="largerCategories"
                            @update:modelValue="chooseLargerCategoryItem"
                            label="Larger Category"
                            multiple
                            chips
                        ></v-select>
                        </v-col>
                        <v-col cols="4">
                            <v-select
                                v-model="combinationsChosen"
                                :items="combinaitons"
                                @update:modelValue="chooseCombinationItem"
                                label="WM/CM"
                                multiple
                                >
                                <template v-slot:selection="{ item, index }">
                                    <v-chip v-if="index < 20" :text="item.title"></v-chip>
                                        <span
                                        v-if="index === 20"
                                        class="text-grey text-caption align-self-center"
                                        >
                                        (+{{ this.combinationsChosen.length - 20 }} others)
                                        </span>
                                </template>
                            </v-select>
                        </v-col>
                    </v-row>
                </v-card>
            </v-menu>
        </v-col>
        <v-col cols="5">
            <v-menu :close-on-content-click="false" location="end">
                <template v-slot:activator="{ props: activatorProps }">
                    <v-btn
                        v-bind="activatorProps"
                        prepend-icon="mdi-calendar-question"
                        text="Show Undated ▶"
                        size="x-large" rounded="xl" class="ml-6"
                        :color="chymistryPrimaryColor"
                        @click="listUndated"
                        >
                    </v-btn>
                </template>
                <v-card elevated width="220" min-height="250" max-height="1000">
                    <v-card-text class="text-caption">
                        <ul>
                            <li v-for= "item in filteredUndatedItems">
                                {{item}}
                            </li>
                        </ul>
                    </v-card-text>
                </v-card>
            </v-menu>
        </v-col>
    </v-row>
    <v-row class="ml-n12">
        <v-col>
            <v-sheet width="250">
                <canvas style="margin-top: 10px;" id="myCanvas" :width="width" :height="height+vMargin*2"/>
            </v-sheet>
        </v-col>
        <v-col>
            <v-sheet width="300">
                <div class="text-caption" v-for= "(itemHeight, index) in itemVLocations">
                    <div :style="'position: absolute; top: ' + itemHeight + 'px;'">
                    {{itemStrings[index]}}
                    </div>
                </div>
            </v-sheet>
        </v-col>
        <v-col>
            <v-sheet width="100" class="ml-n7">
                <div class="text-caption" v-for= "(itemHeight, index) in itemVLocations">
                    <div :style="'position: absolute; top: ' + itemHeight + 'px;'">
                    {{itemStringsWaterMark[index]}}
                    </div>
                </div>
            </v-sheet>
        </v-col>
    </v-row>
</v-container>
</template>
<script>
export default {
  name: "shapirowatermark",
  setup() {
    return {
      range: ref({
        min: 1690,
        max: 1695
      })
    }
  },
  mounted: function () {
    axios.get("/js/vue-component/json-data/watermark-data.json")
      .then(response => {
        this.wmdata = []
        this.undatedData = []
        for (let item of response.data) {
          if (item.jdatebegin === "" && item.jdateend === "") {
            this.undatedData.push(item)
            let combi =  item.watermark + "/" + item.countermark
            let str = item.shelf + " " + item.face + " " + combi
            this.filteredUndatedItems.push(str)
          } else {
            this.wmdata.push(item)
          }
        }
        axios.get("/js/vue-component/json-data/julian-number.json")
          .then(response => {
            this.julianNumber = response.data
            this.drawTimeline()
          })
      })
    axios.get("/js/vue-component/json-data/tree.json")
      .then(response => {
            this.tree = response.data
            this.treeIntoArrays()
      }).catch((error) => alert(error))
  },
  methods: {
    drawTimeline: function() {
      // Initialization
      this.itemVLocations.splice(0)
      this.itemStrings.splice(0)
      this.itemStringsWaterMark.splice(0)
      const duration = this.range.max - this.range.min
      const c = document.getElementById("myCanvas")
      const context = c.getContext('2d')

      let minJDate = this.julianNumber.find(n => n.year == this.range.min).number
      let maxJDate = this.julianNumber.find(n => n.year == this.range.max).number-1
      let daysShownInTimeline = maxJDate - minJDate
      let ratio = this.height/daysShownInTimeline

      // Draw axis
      context.clearRect(0, 0, this.width, this.height+this.vMargin*2)
      context.beginPath()
      context.moveTo(this.hMargin,this.vMargin)
      context.lineTo(this.hMargin,this.vMargin+this.height)
      context.strokeStyle = this.chymistryPrimaryColor
      context.lineWidth = 5
      context.stroke()

      for (var i = 0; i <= duration; i++) {
        context.beginPath()
        context.arc(this.hMargin, this.vMargin+this.height/duration*i, 7, 0, 2 * Math.PI)
        context.fillStyle = this.chymistryPrimaryColor
        context.fill()

        var distanceBetweenNewYearToMar31 = this.height/duration/12/4
        for (var j = 0; j < 12; j++) {
          if (i<duration) {
            context.beginPath()
            if (j === 1) {

            }
            context.moveTo(this.hMargin,
              this.vMargin
              + this.height/duration*i
              + distanceBetweenNewYearToMar31
              + this.height/duration/12*j)
            context.lineTo(this.hMargin-10,
              this.vMargin
              + this.height/duration*i
              + distanceBetweenNewYearToMar31
              + this.height/duration/12*j)
            context.strokeStyle = this.chymistryPrimaryColor
            context.lineWidth = 2
            context.stroke()
          }
        }

        context.font = "24pt sans-serif"
        context.textBaseline = "middle"
        context.textAlign = "left"
        let yr = this.range.min + i
        context.fillText(yr, 15, this.vMargin+this.height/duration*i)
      }

      // Draw lines and items
      var previousHeight = 0
      for (var i = 0; i < this.wmdata.length; i++) {
        //Ignore Duplications
        if (i > 0 && this.wmdata[i].NPID === this.wmdata[i-1].NPID) {
          continue
        }
        //Filter items
        if (!this.isFirstLoad) {
          let combi =  this.wmdata[i].watermark + "/" + this.wmdata[i].countermark
          if (!this.combinationsChosen.includes(combi)) {
            continue
          }
        }
        let dateStart = this.wmdata[i].jdatebegin
        let dateEnd = this.wmdata[i].jdateend
        if (dateStart === "" || dateStart < minJDate || dateEnd > maxJDate) {
          continue
        }
        let daysFromMin = dateStart - minJDate
        let distanceFromMin = (this.height*daysFromMin/daysShownInTimeline)
        let yPoint = this.vMargin+distanceFromMin
        let adjustedYPoint = this.vMargin+distanceFromMin
        if (yPoint-previousHeight<10) {
          adjustedYPoint = yPoint + 10 - (yPoint-previousHeight)
        }
        context.beginPath()
        context.arc(this.hMargin, yPoint, 3, 0, 2 * Math.PI)
        context.fillStyle = "blue"
        context.fill()

        if (dateStart == dateEnd) {
          context.beginPath()
          context.moveTo(this.hMargin, yPoint)
          context.lineTo(this.hMargin+this.lineLength, adjustedYPoint)
          context.strokeStyle = "blue"
          context.lineWidth = 1
          context.stroke()
        } else {
          let daysFromMinToEnd = dateEnd - minJDate
          let distanceFromMinToEnd = (this.height*daysFromMinToEnd/daysShownInTimeline)
          let endYPoint = this.vMargin + distanceFromMinToEnd
          context.beginPath()
          context.moveTo(this.hMargin, yPoint)
          context.lineTo(this.hMargin+this.lineLength, adjustedYPoint)
          context.lineTo(this.hMargin, endYPoint)
          context.strokeStyle = "red"
          context.lineWidth = 1
          context.stroke()
        }
        this.itemStrings.push(this.wmdata[i].date.substr(0,20)+" "+this.wmdata[i].document.substr(0,25))
        this.itemStringsWaterMark.push(this.wmdata[i].shapirocode)
        this.itemVLocations.push(adjustedYPoint+this.vMargin+this.chymistryHeaderHeight)
        previousHeight = adjustedYPoint
      }
      this.itemVLocations.splice(this.itemVLocations.length)
      this.canvas = context
      this.listUndated()
      this.isFirstLoad = false
    },
    listUndated: function () {
      this.filteredUndatedItems.splice(0)
      for (var i = 0; i < this.undatedData.length; i++) {
        if (!this.isFirstLoad) {
          let combi =  this.undatedData[i].watermark + "/" + this.undatedData[i].countermark
          if (!this.combinationsChosen.includes(combi)) {
            continue
          }
          let str = this.undatedData[i].shelf + " " + this.undatedData[i].face + " " + combi
          this.filteredUndatedItems.push(str)
        }
      }
    },
    setMaxMinHeight: function() {
      this.range.min = this.duration[0]
      this.range.max = this.duration[1]
      let gap = this.range.max - this.range.min
      this.minHeight = gap/5*1000
      this.maxHeight = gap*1000
      this.height = gap/5*1000*2
      this.sliderStep = gap/5*1000/4

      this.$nextTick(() => (this.drawTimeline()))
    },
    refreshCanvas: function() {
      this.$nextTick(() => (this.drawTimeline()))
    },
    treeIntoArrays: function() {
      var prevLargerCategory = ""
      var prevCombination = ["",""]
      for (let item of this.tree) {
        if (item.largergroup != prevLargerCategory) {
          this.largerCategories.push(item.largergroup)
        }
        if (item.watermark != prevCombination[0] || item.countermark != prevCombination[1]) {
          let str = item.watermark + "/" + item.countermark
          this.combinaitons.push(str)
        }
        prevLargerCategory = item.largergroup
        prevCombination[0] = item.watermark
        prevCombination[1] = item.countermark
      }
      this.combinaitons = [...new Set(this.combinaitons)]

      this.largerCategoriesChosen = [... this.largerCategories]
      this.combinationsChosen = [...this.combinaitons]
      this.prevLargerCategoriesChosen = [...this.largerCategoriesChosen]
      this.prevCombinationsChosen = [...this.combinationsChosen]
    },
    selectAllFilteringKeywords: function() {
      this.largerCategoriesChosen = [...this.largerCategories]
      this.combinationsChosen = [...this.combinaitons]
      this.prevLargerCategoriesChosen = [...this.largerCategoriesChosen]
      this.prevCombinationsChosen = [...this.combinationsChosen]
      this.$nextTick(() => (this.drawTimeline()))
    },
    unselectAllFilteringKeywords: function() {
      this.largerCategoriesChosen.splice(0)
      this.combinationsChosen.splice(0)
      this.prevLargerCategoriesChosen = [...this.largerCategoriesChosen]
      this.prevCombinationsChosen = [...this.combinationsChosen]
      this.$nextTick(() => (this.drawTimeline()))
    },
    chooseLargerCategoryItem: function() {
      if (this.largerCategoriesChosen.length > this.prevLargerCategoriesChosen.length) {
        for (let item of this.tree) {
          if (this.largerCategoriesChosen.includes(item.largergroup)) {
            let combi = item.watermark + "/" + item.countermark
            if (!this.combinationsChosen.includes(combi)) {
              this.combinationsChosen.push(combi)
            }
          }
        }
      } else {
        for (let lc of this.prevLargerCategoriesChosen) {
          if (!this.largerCategoriesChosen.includes(lc)) {
            for (let item of this.tree) {
              if (lc === item.largergroup ) {
                let combi = item.watermark + "/" + item.countermark
                let deleteIndex = this.combinationsChosen.findIndex((c) => c === combi)
                this.combinationsChosen.splice(deleteIndex,1)
              }
            }
          }
        }
      }
      this.prevLargerCategoriesChosen = [...this.largerCategoriesChosen]
      this.$nextTick(() => (this.drawTimeline()))
    },
    chooseCombinationItem: function() {
      if (this.combinationsChosen.length <=this.prevCombinationsChosen.length) {
        for (let combi of this.prevCombinationsChosen) {
          if (!this.combinationsChosen.includes(combi)) {
            for (let item of this.tree) {
              let cb = item.watermark + "/" + item.countermark
              if (cb === combi) {
                let lg = item.largergroup
                let deleteIndex = this.largerCategoriesChosen.findIndex((c) => c === lg)
                this.combinationsChosen.splice(deleteIndex,1)
              }
            }
          }
        }
      } else {
        let lg = ""
        for (let combi of this.combinationsChosen) {
          if (!this.prevCombinationsChosen.includes(combi)) {
            for (let item of this.tree) {
              let cb = item.watermark + "/" + item.countermark
              if (cb === combi) {
                lg = item.largergroup
                break
              }
            }
          }
        }
        var flg = false
        for (let item of this.tree) {
          if (lg === item.largergroup) {
            let cb = item.watermark + "/" + item.countermark
            if (!this.combinationsChosen.includes(cb)) {
              flg = false
              break
            }
            flg = true
          }
        }
        if (flg && !this.largerCategoriesChosen(lg)) {
          this.largerCategoriesChosen.push(lg)
        }
      }
      this.prevCombinationsChosen = [...this.combinationsChosen]
      this.$nextTick(() => (this.drawTimeline()))
    },
  },
  data() {
    return {
      wmdata: null,
      undatedData: null,
      tree: null,
      julianNumber: null,
      chymistryHeaderHeight: 288,
      vMargin: 40,
      hMargin: 100,
      height: 2000,
      width: 280,
      minHeight: 1000,
      maxHeight: 5000,
      sliderStep: 250,
      baseMinYear: 1665,
      baseMaxYear: 1727,
      duration:[this.range.min,this.range.max],
      lineLength: 175,
      chymistryPrimaryColor: "#7a1705",
      canvas: null,
      isFirstLoad: true,
      itemVLocations: [],
      itemStrings: [],
      itemStringsWaterMark: [],

      largerCategories: [],
      largerCategoriesChosen: [],
      prevLargerCategoriesChosen: [],
      combinaitons: [],
      combinationsChosen: [],
      prevCombinationsChosen: [],
      filteredUndatedItems: [],
    };
  },
};
</script>
