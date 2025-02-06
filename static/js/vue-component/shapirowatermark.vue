<template>
<v-container>
    <v-row>
        <v-speed-dial
        location="right center"
        transition="fade-transition"
        >
            <template v-slot:activator="{ props: activatorProps }">
                <v-fab v-bind="activatorProps" icon="mdi-cog" size="x-large" class="mt-8" color="primary">
                </v-fab>
            </template>
            <v-card elevated>
                <v-row>
                    <v-col>
                        <v-row>
                            <div class="text-h4">Time Range</div>
                        </v-row>
                        <v-row>
                            <v-range-slider
                                @change="setMaxMinHeight"
                                v-model="range"
                                thumb-label="always"
                                :min="baseMinYear"
                                :max="baseMaxYear"
                            />
                        </v-row>
                    </v-col>
                    <v-col>
                        <v-row>
                            <div class="text-h4">Timeline Height</div>
                        </v-row>
                        <v-row>
                            <v-slider
                                @change="drawTimeline"
                                v-model="height"
                                :step="sliderStep"
                                :label-value="'Height: ' + height + ' px'"
                                thumb-label="always"
                                :min="minHeight"
                                :max="maxHeight"
                            />
                        </v-row>
                    </v-col>
                </v-row>
                <v-row>
                    <v-col>
                        <v-expansion-panels>
                            <v-expansion-panel-title>
                                <v-icon icon="mdi-filter"></v-icon>
                                <span class="text-h5">Filter by Watermark Code</span>
                            </v-expansion-panel-title>
                            <v-expansion-panel-text>
                                <!--フィルタのUI-->
                            </v-expansion-panel-text>
                        </v-expansion-panels>
                    </v-col>
                </v-row>
            </v-card>
        </v-speed-dial>
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
            <v-sheet width="100">
                <div class="text-caption" v-for= "(itemHeight, index) in itemVLocations">
                    <div :style="'position: absolute; top: ' + itemHeight + 'px;'">
                    {{itemStringsWaterMark[index]}}
                    </div>
                </div>
            </v-sheet>
        </v-col>
        <v-col>
            <v-sheet>
                <!--TODO　フローティングパネル、配列をdataから移して表示用配列を作る、フィルターするメソッドを作る-->
                <!-- <div class="text-h6" v-for= "item in mss3958Data">
                    <a v-if="doesWaterMarkMatch(item.code)" href="item.url">{{ item.shelfNo }}, {{ item.page }}</a>
                </div> -->
                <!-- <div class="text-h6" v-for= "item in filteredAdditionalMSS">
                    <a href="item.url">{{ item.shelfNo }}, {{ item.page }} ({{ item.code }})</a>
                </div> -->
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
    // axios.get("/js/vue-component/json-data/watermark-data.json").then(response => (this.wmdata = response)).then(this.drawTimeline())
    axios.get("/js/vue-component/json-data/watermark-data.json")
      .then(response => {
        this.wmdata = response.data
        this.drawTimeline()
      })
    axios.get("/js/vue-component/json-data/tree.json")
      .then(response => { this.tree = response.data }).catch((error) => alert(error))
    // this.createFilteringKeywords()
  },
  methods: {
    drawTimeline: function() {
      this.itemVLocations.splice(0)
      this.itemStrings.splice(0)
      this.itemStringsWaterMark.splice(0)
      const duration = this.range.max - this.range.min
      const totalDays = this.getDays(this.range.min,"03","25",this.range.max,"03","25")
      const c = document.getElementById("myCanvas")
      const context = c.getContext('2d')
      context.clearRect(0, 0, this.width, this.height+this.vMargin*2)
      context.beginPath()
      context.moveTo(this.hMargin,this.vMargin)
      context.lineTo(this.hMargin,this.vMargin+this.height)
      context.strokeStyle = "#00c2bc"
      context.lineWidth = 5
      context.stroke()

      for (var i = 0; i <= duration; i++) {
        context.beginPath()
        context.arc(this.hMargin, this.vMargin+this.height/duration*i, 7, 0, 2 * Math.PI)
        context.fillStyle = "#00c2bc"
        context.fill()

        var intervalsSum = this.height/duration/12/4
        for (var j = 0; j < 12; j++) {
          if (i<duration) {
            context.beginPath()
            if (j === 1) {

            }
            context.moveTo(this.hMargin,this.vMargin+this.height/duration*i + intervalsSum+ this.height/duration/12*j)
            context.lineTo(this.hMargin-10,this.vMargin+this.height/duration*i + intervalsSum+ this.height/duration/12*j)
            context.strokeStyle = "#00c2bc"
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

      const regexDay = new RegExp("[0-9]{1,2}")
      // const regexMonth = new RegExp("[a-zA-Z]+")
      const regexYear = new RegExp("[0-9]{4}")
      const regexRange = new RegExp("[0-9]{4}\/[0-9]+")
      var previousHeight = 0
      for (var i = 0; i < this.wmdata.length; i++) {
        if (!this.isFirstLoad) {
          var isFound = false
          for (var filteringItem of this.broaderCategoryChoices) {
          // for (var filteringItem of this.broaderCategoryChoices) {
            // if (filteringItem.includes(this.wmdata[i].watermark_code)) {
            if (this.wmdata[i].watermark_code.includes(filteringItem)) {
              isFound = true
              // TODO 多分ここで該当したコードをdata作った配列に入れる？
              break
            }
          }
          if (!isFound) {
            continue
          }
        }
        let date = this.wmdata[i].date
        let cleanedDate = date.replace(/[\[\]\.\?]/g,"")
        let dateArray = cleanedDate.split(/\s/)
        var year = ""
        var month = ""
        var day = ""
        var day2 = ""
        for (var j = 0; j < dateArray.length; j++) {
          if (regexYear.test(dateArray[j])) {
            if (regexRange.test(dateArray[j])) {
              let yearArray = dateArray[j].split("\/")
              year = String(parseInt(yearArray[0])+1)
            } else {
              year = dateArray[j]
            }
          } else if (this.convertMonthToNum(dateArray[j]) !== "") {
            month = this.convertMonthToNum(dateArray[j])
          } else if (regexDay.test(dateArray[j])) {
            day = dateArray[j]
          }
        }
        if (year === "" || year < this.range.min || year >= this.range.max) {
          continue
        }
        if (month === "") {
          month = "03"
        }
        if (day === "") {
          day = "01"
          day2 = "0"
        }

        let daysFromStart = this.getDays(this.range.min,"03","25",year, month, day)
        let ratio = daysFromStart / totalDays
        let distanceFromStart = (this.height*ratio)
        let yPoint = this.vMargin+distanceFromStart
        let adjustedYPoint = this.vMargin+distanceFromStart
        if (yPoint-previousHeight<10) {
          adjustedYPoint = yPoint + 10 - (yPoint-previousHeight)
        }
        context.beginPath()
        context.arc(this.hMargin, yPoint, 3, 0, 2 * Math.PI)
        context.fillStyle = "blue"
        context.fill()

        if (day2 !== "0") {
          context.beginPath()
          context.moveTo(this.hMargin, yPoint)
          context.lineTo(this.hMargin+this.lineLength, adjustedYPoint)
          context.strokeStyle = "blue"
          context.lineWidth = 1
          context.stroke()
        } else {
          let daysFromStartToEnd = this.getDays(this.range.min,"03","25",year, parseInt(month)+1, day2)
          let ratioToEnd = daysFromStartToEnd / totalDays
          let distanceFromStartToEnd = (this.height*ratioToEnd)
          context.beginPath()
          context.moveTo(this.hMargin,yPoint)
          // Adjusting height to that of the end of the range - Data needs to be sorted by date to render properly.
          // adjustedYPoint = this.vMargin+distanceFromStartToEnd
          context.lineTo(this.hMargin+this.lineLength, adjustedYPoint)
          context.lineTo(this.hMargin, this.vMargin+distanceFromStartToEnd)
          context.strokeStyle = "red"
          context.lineWidth = 1
          context.stroke()
        }

        // context.font = "8pt sans-serif"
        // context.textBaseline = "middle"
        // context.textAlign = "left"
        // context.fillText(this.wmdata[i].date+" "+this.wmdata[i].document, 255, adjustedYPoint)
        this.itemStrings.push(this.wmdata[i].date+" "+this.wmdata[i].document)
        this.itemStringsWaterMark.push(this.wmdata[i].shapirocode)
        this.itemVLocations.push(adjustedYPoint)
        previousHeight = adjustedYPoint
      }
      this.itemVLocations.splice(this.itemVLocations.length-1)
      this.canvas = context;
      this.isFirstLoad = false

      // this.filterMSS()
    },
    getDays: function(startYear,startMonth,startDay,endYear,endMonth,endDay) {
      let startDate = new Date(startYear,startMonth,startDay)
      let endDate = new Date(endYear,endMonth,endDay)
      return ((endDate-startDate)/86400000)
    },
    setMaxMinHeight: function() {
      let gap = this.range.max - this.range.min
      this.minHeight = gap/5*1000
      this.maxHeight = gap*1000
      this.height = gap/5*1000*2
      this.sliderStep = gap/5*1000/4

      this.$nextTick(() => (this.drawTimeline()))
    },
    convertMonthToNum: function(month) {
      const monthDic = {"January":"01","February":"02","March":"03","April":"04",
        "May":"05","June":"06","July":"07","August":"08","September":"09","October":"10",
        "November":"11","December":"12"
      }
      if (monthDic[month]) {
        return monthDic[month]
      }
      return ""
    },
    createFilteringKeywords: function() {
      var tempArray = []
      var tempArray2 = []
      // for (var item of this.wmdata) {
      //   tempArray.push(item.watermark_code)
      // }
      for (var i = 0; i < this.watermarkComponents.length; i++) {
        if (this.watermarkComponents[i].broaderCategory === this.watermarkComponents[i+1].broaderCategory) {
          tempArray.push(this.watermarkComponents[i].code)
          tempArray2.push(this.watermarkComponents[i].name)
          this.watermarkMainComponentCodes.push(this.watermarkComponents[i].code)
          if (i == this.watermarkComponents.length - 2) {
            tempArray.push(this.watermarkComponents[i+1].code)
            tempArray2.push(this.watermarkComponents[i+1].name)
            this.watermarkMainComponentCodes.push(this.watermarkComponents[i+1].code)
            this.broaderCategories.push(this.watermarkComponents[i+1].broaderCategory)
            let item = { broaderCategory: this.watermarkComponents[i+1].broaderCategory, codes: tempArray, names: tempArray2 }
            this.structuredWatermarkCodeData.push(item)
            tempArray = []
            tempArray2 = []
            break
          }
          continue
        } else {
          tempArray.push(this.watermarkComponents[i].code)
          tempArray2.push(this.watermarkComponents[i].name)
          this.watermarkMainComponentCodes.push(this.watermarkComponents[i].code)
          let item = { broaderCategory: this.watermarkComponents[i].broaderCategory, codes: tempArray, names: tempArray2 }
          this.broaderCategories.push(this.watermarkComponents[i].broaderCategory)
          this.structuredWatermarkCodeData.push(item)
          tempArray = []
          tempArray2 = []
          if (i == this.watermarkComponents.length - 2) {
            let item = { broaderCategory: this.watermarkComponents[i+1].broaderCategory, codes: [this.watermarkComponents[i+1].code], names: [this.watermarkComponents[i+1].name] }
            this.watermarkMainComponentCodes.push(this.watermarkComponents[i+1].code)
            this.broaderCategories.push(this.watermarkComponents[i+1].broaderCategory)
            this.structuredWatermarkCodeData.push(item)
            break
          }
        }
      }
      // var uniqueArray = [...new Set(this.structuredWatermarkCodeData)].sort()

      // var midArray = []
      // for (var item of uniqueArray) {
      //   var keywords = item.split(/[\/\+]/)
      //   for (var keyword of keywords) {
      //     var str = keyword.trim()
      //     if (str != "") {
      //       midArray.push(str)
      //     }
      //   }
      // }
      // this.broaderCategories = [...new Set(midArray.sort())]
      // this.broaderCategoryChoices = [...new Set(midArray)]

      // this.broaderCategories = uniqueArray
      // this.broaderCategoryChoices = uniqueArray
      this.broaderCategoryChoices = this.broaderCategories
      this.codeChoices = this.watermarkMainComponentCodes
      this.countermarkChoises = this.countermarks
      // console.log(this.broaderCategoryChoices);
      // console.log(this.codeChoices);
      // console.log(this.structuredWatermarkCodeData);

      // this.filterMSS()
    },
    selectAllFilteringKeywords: function() {
      this.broaderCategoryChoices = this.broaderCategories
      this.codeChoices = this.watermarkMainComponentCodes
      this.countermarkChoises = this.countermarks
      this.setMaxMinHeight()
    },
    unselectAllFilteringKeywords: function() {
      this.broaderCategoryChoices = []
      this.codeChoices = []
      this.countermarkChoises = []
      this.setMaxMinHeight()
    },
    chooseRelevantComponents: function(broaderCategory) {
      let ind = -1
      for (var i = 0; i < this.structuredWatermarkCodeData.length; i++) {
        if (this.structuredWatermarkCodeData[i].broaderCategory === broaderCategory) {
          ind = i
          break
        }
      }
      if (this.broaderCategoryChoices.includes(broaderCategory)) {
        for (var j = 0; j < this.structuredWatermarkCodeData[ind].codes.length; j++) {
          let index = this.codeChoices.indexOf(this.structuredWatermarkCodeData[ind].codes[j])
          this.codeChoices.splice(index, 1)
        }
      } else {
        for (var j = 0; j < this.structuredWatermarkCodeData[ind].codes.length; j++) {
          console.log(this.structuredWatermarkCodeData[ind].codes[j]);
          this.codeChoices.push(this.structuredWatermarkCodeData[ind].codes[j])
        }
      }

      this.$nextTick(() => (this.drawTimeline()))
    },
    // doesWaterMarkMatch: function() {
    //   self = this
    //   return function (item){
    //     for (var i = 0; i < this.broaderCategoryChoices.length; i++) {
    //       if (item.indexOf(this.broaderCategoryChoices[i]) > -1) {
    //         // console.log(item);
    //         return true
    //       }
    //     }
    //     return false
    //   }
    // },
    filterMSS: function() { // TODO タイムラインに表示されているものだけを対象にして絞り込むようにする
      this.filteredAdditionalMSS.splice(0)
      for (var i = 0; i < this.mss3958Data.length; i++) {
        for (var j = 0; j < this.broaderCategoryChoices.length; j++) {
          if (!this.mss3958Data[i].code) {
            continue
          }
          if (this.mss3958Data[i].code.toUpperCase().indexOf(this.broaderCategoryChoices[j]) > -1) {
            this.filteredAdditionalMSS.push(this.mss3958Data[i])
          }
        }
      }
    },
  },
  data() {
    return {
      wmdata: null,
      tree: null,
      vMargin: 40,
      hMargin: 100,
      height: 2000,
      width: 280,
      minHeight: 1000,
      maxHeight: 5000,
      sliderStep: 250,
      baseMinYear: 1661,
      baseMaxYear: 1727,
      lineLength: 175,
      canvas: null,
      isFirstLoad: true,
      itemVLocations: [],
      itemStrings: [],
      itemStringsWaterMark: [],

    };
  },
};
</script>
