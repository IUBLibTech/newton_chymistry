<template>
    <v-stepper ref="stepper" :items="steps" hide-actions>
        <!--Search Type-->
        <template v-slot:item.1>
            <v-card :title="steps[0]" flat>
                <v-row>
                    <v-col>
                        <h5>Search Type</h5>
                        <v-radio-group
                            v-model="searchConditions.step1Type"
                            @update:modelValue="searchTypeChosen"
                        >
                            <div v-for="(type, index) in searchTypes">
                                <v-radio
                                    :label="type.type"
                                    :value="index"
                                    :disabled="type.disabled"
                                ></v-radio>
                            </div>
                        </v-radio-group>
                    </v-col>
                    <v-col>
                        <h5>Chunk Size</h5>
                        <v-radio-group
                            v-model="searchConditions.step1Size"
                            @update:modelValue="chunkSizeChosen"
                        >
                            <div v-for="(size, index) in chunkSizes">
                                <v-radio
                                    :label="size.size"
                                    :value="index"
                                    :disabled="size.disabled"
                                ></v-radio>
                            </div>
                        </v-radio-group>
                    </v-col>
                </v-row>
            </v-card>
        </template>

        <!--Result Output Type-->
        <template v-slot:item.2>
            <v-card :title="steps[1]" flat>
                <v-radio-group
                    v-model="searchConditions.step2"
                    @update:modelValue="resultOutputTypeChosen"
                >
                    <div v-for="(type, index) in resultOutputTypes">
                        <v-radio
                            :label="type.type"
                            :value="index"
                            :disabled="type.disabled"
                        ></v-radio>
                    </div>
                </v-radio-group>
            </v-card>
        </template>

        <!--Return Scope of Pairs-->
        <template v-slot:item.3>
            <v-card :title="steps[2]" flat>
                <v-radio-group
                    v-model="searchConditions.step3"
                    @update:modelValue="returnScopesOfPairChosen"
                >
                    <div v-for="(scope, index) in returnScopesOfPairs">
                        <v-radio
                            :label="scope.scope"
                            :value="index"
                            :disabled="scope.disabled"
                        ></v-radio>
                    </div>
                </v-radio-group>
            </v-card>
        </template>

        <!--Documents-->
        <template v-slot:item.4>
            <v-row>
                <v-col>
                    <v-card :title="steps[3]" flat>
                    <v-btn @click="getDocuments" >LIST</v-btn>
                    <div>{{documents}}</div>
                    <!-- <div v-for="title in documents">
                        {{title}}
                    </div> -->
                    <!-- list on the left, v-chip will be used for chosen docs
                        textbox for regex search -->
                    </v-card>
                </v-col>
                <v-col></v-col>
            </v-row>
        </template>

        <!--Threshold-->
        <template v-slot:item.5>
            <v-card :title="steps[4]" flat>
                <v-radio-group>
                    <div v-for="(threshold, index) in thresholds">
                        <v-radio
                            :label="threshold.value"
                            :value="index"
                        ></v-radio>
                    </div>
                </v-radio-group>
            </v-card>
        </template>
        <v-stepper-actions
            :disabled="nextDisabled"
            :next-text="labelBtnNext"
            @click:next="clickNext"
            @click:prev="clickPrev"
        ></v-stepper-actions>
    </v-stepper>
</template>
<script>
export default {
  name: "lsa",
  methods: {
    clickNext: function () {
      if (this.labelBtnNext == "Next") {
        this.$refs.stepper.next();
        this.currentStep++;
        this.isCurrentStepCompleted();
        console.log(this.nextDisabled);
        if (this.currentStep > 5) {
            this.labelBtnNext = "Submit";
        }
      } else {
          this.runQuery();
      }
    },
    clickPrev: function () {
      this.$refs.stepper.prev();
      this.currentStep--;
      this.isCurrentStepCompleted;
      if (this.currentStep == 1) {
        this.nextDisabled = "prev"
      }
    },
    isCurrentStepCompleted: function () {
      console.log(this.currentStep);
      switch (this.currentStep) {
        case 1:
          if (
            this.searchConditions.step1Type > -1 &&
            this.searchConditions.step1Size > -1
          ) {
            this.nextDisabled = false;
          } else {
            this.nextDisabled = "next";
          }
          break;
        case 2:
          if (this.searchConditions.step2 > -1) {
            this.nextDisabled = false;
          } else {
            this.nextDisabled = "next";
          }
          break;
        case 3:
          if (this.searchConditions.step3 > -1) {
            this.nextDisabled = false;
          } else {
            this.nextDisabled = "next";
          }
          break;
        case 4:
          if (this.searchConditions.step4.size > 0) {
            this.nextDisabled = false;
          } else {
            this.nextDisabled = "next";
          }
          break;
        case 5:
          if (this.searchConditions.step5 > -1) {
            this.nextDisabled = false;
          } else {
            this.nextDisabled = "next";
          }
          break;
      }
    },
    searchTypeChosen: function () {
      this.searchConditions.step2 =  -1
      this.searchConditions.step3 =  -1
      this.searchConditions.step4 =  []
      this.searchConditions.step5 =  -1
      switch (this.searchConditions.step1Type) {
        case 0: //Document-Document
          for (let i = 0; i < this.resultOutputTypes.length; i++) {
              if (i == 0 || i == 1 || i == 4) { //Descending Order, One Doc in Page Order, Graph for NWB
                  this.resultOutputTypes[i].disabled = false;
                  for ( let j = 0; j < this.returnScopesOfPairs.length; j++ ) {
                      if (j == 0 || j == 1 || j == 2) { // All Above Chosen Value, All Between Docs or Terms, Within One Document (Doc-Doc)
                        this.returnScopesOfPairs[j].disabled = false;
                      } else {
                        this.returnScopesOfPairs[j].disabled = true;
                      }
                  }
              } else {
                  this.resultOutputTypes[i].disabled = true;
              }
          }
          break;
        case 1: //Chunk-Chunk
          for (let i = 0; i < this.resultOutputTypes.length; i++) {
              if (i == 0 || i == 4) { // Descending Order, Graph for NWB
                  this.resultOutputTypes[i].disabled = false;
                  for ( let j = 0; j < this.returnScopesOfPairs.length; j++ ) {
                      if (j == 0) { // All Above Chosen Value
                          this.returnScopesOfPairs[j].disabled = false;
                      } else {
                        this.returnScopesOfPairs[j].disabled = true;
                      }
                  }
              } else {
                  this.resultOutputTypes[i].disabled = true;
              }
          }
          break;
        case 2: //Term-Term
          for (let i = 0; i < this.resultOutputTypes.length; i++) {
              if (i == 0 || i == 4) { // Descending Order, Graph for NWB
                  this.resultOutputTypes[i].disabled = false;
                  for ( let j = 0; j < this.returnScopesOfPairs.length; j++ ) {
                      if (j == 0 || j == 1) { // All Above Chosen Value, All Between Docs or Terms
                          this.returnScopesOfPairs[j].disabled = false;
                      } else {
                        this.returnScopesOfPairs[j].disabled = true;
                      }
                  }
              } else {
                  this.resultOutputTypes[i].disabled = true;
              }
          }
          break;
        case 3: //Compose Query w/Terms
          for (let i = 0; i < this.resultOutputTypes.length; i++) {
              if (i == 0) { // Descending Order
                  this.resultOutputTypes[i].disabled = false;
                  for ( let j = 0; j < this.returnScopesOfPairs.length; j++ ) {
                      if (j == 0 || j == 4 || j == 5) { // All Above Chosen Value, All w/Term Presence (Term ↔ Doc), Only if Term Present (Term ↔ Doc)
                          this.returnScopesOfPairs[j].disabled = false;
                      } else {
                        this.returnScopesOfPairs[j].disabled = true;
                      }
                  }
              } else {
                  this.resultOutputTypes[i].disabled = true;
              }
          }
          break;
        case 4: //Compose Query w/Chunks
          for (let i = 0; i < this.resultOutputTypes.length; i++) {
              if (i == 0) { // Descending Order
                  this.resultOutputTypes[i].disabled = false;
                  for ( let j = 0; j < this.returnScopesOfPairs.length; j++ ) {
                      if (j == 0) { // All Above Chosen Value
                          this.returnScopesOfPairs[j].disabled = false;
                      } else {
                        this.returnScopesOfPairs[j].disabled = true;
                      }
                  }
              } else {
                  this.resultOutputTypes[i].disabled = true;
              }
          }
          break;
        default:
          for (let i = 0; i < this.resultOutputTypes.length; i++) {
              this.resultOutputTypes[i].disabled = true;
          }
          for (let i = 0; i < returnScopesOfPairs.length; i++) {
              this.returnScopesOfPairs[i].disabled = true;
          }
      }
      if (this.searchConditions.step1Type > -1 && this.searchConditions.step1Size > -1) {
        this.nextDisabled = "prev";
      }
    },

    chunkSizeChosen: function () {
      if (
        this.searchConditions.step1Type > -1 &&
        this.searchConditions.step1Size > -1
      ) {
        this.nextDisabled = "prev";
      }
    },

    resultOutputTypeChosen: function () {
      if (this.searchConditions.step2 > -1) {
        this.nextDisabled = false;
      }
    },

    returnScopesOfPairChosen: function () {
      if (this.searchConditions.step3 > -1) {
        this.nextDisabled = false;
      }
    },

    getDocuments: function() {
      axios
        .get('https://alchemy.sitehost-test.iu.edu/lsa/connectiontest.php')
        .then(response => (this.documents = response))
    },

    runQuery: function () {
        //Running SQL query by sending HTTP requests.
    },
  },
  data() {
    return {
      labelBtnNext: "Next",
      currentStep: 1,
      nextDisabled: true,
      searchConditions: {
        step1Type: -1,
        step1Size: -1,
        step2: -1,
        step3: -1,
        step4: [],
        step5: -1,
      },
      steps: [
        "Search Type",
        "Result Output Type",
        "Return Scope of Pairs",
        "Documents",
        "Threshold",
      ],
      searchTypes: [
        { type: "Document-Document", disabled: false },
        { type: "Chunk-Chunk", disabled: false },
        { type: "Term-Term", disabled: false },
        // { type: "Term-Chunk", disabled: false },
        // { type: "Chunk-Term", disabled: false },
        { type: "Compose Query w/Terms", disabled: false },
        { type: "Compose Query w/Chunks", disabled: false },
      ],
      chunkSizes: [
        { size: "250-word Chunks", disabled: false },
        { size: "1000-word Chunks", disabled: false },
      ],
      resultOutputTypes: [
        { type: "Descending Order", disabled: false },
        { type: "One Doc in Page Order", disabled: false },
        { type: "Term Alpha Order", disabled: false },
        { type: "Doc Catalog Order", disabled: false },
        { type: "Graph for NWB", disabled: false },
        { type: "CSV: XY Term ↔ Doc", disabled: false },
      ],
      returnScopesOfPairs: [
        { scope: "All Above Chosen Value", disabled: false },
        { scope: "All Between Docs or Terms", disabled: false },
        { scope: "Within One Document (Doc-Doc)", disabled: false },
        { scope: "All w/Term Presence (Term ↔ Doc)", disabled: false },
        { scope: "Only if Term Present (Term ↔ Doc)", disabled: false },
      ],
      documents: null,
      thresholds: [
        { value: "0.0", disabled: false },
        { value: "0.1", disabled: false },
        { value: "0.2", disabled: false },
        { value: "0.3", disabled: false },
        { value: "0.4", disabled: false },
        { value: "0.5", disabled: false },
        { value: "0.6", disabled: false },
        { value: "0.7", disabled: false },
        { value: "0.8", disabled: false },
        { value: "0.9", disabled: false },
      ],
    };
  },
};
</script>
