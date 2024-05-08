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
            switch (this.searchConditions.step1Type) {
                case 0: //Document-Document
                    for (let i = 0; i < this.resultOutputTypes.size; i++) {
                        if (i == 2 || i == 3 || i == 5) {
                            this.resultOutputTypes[i].disabled = true;
                        } else {
                            this.resultOutputTypes[i].disabled = false;
                        }
                    }
                    for (let i = 0; i < this.returnScopesOfPairs.size; i++) {
                        if (i == 3 || i == 4) {
                            this.returnScopesOfPairs[i].disabled = true;
                        } else {
                            this.returnScopesOfPairs[i].disabled = false;
                        }
                    }
                    break;
                case 1: //Chunk-Chunk
                    for (let i = 0; i < this.resultOutputTypes.size; i++) {
                        if (i == 1 || i == 2 || i == 3 || i == 5) {
                            this.resultOutputTypes[i].disabled = true;
                        } else {
                            this.resultOutputTypes[i].disabled = false;
                        }
                    }
                    for (let i = 0; i < this.returnScopesOfPairs.size; i++) {
                        this.returnScopesOfPairs[i].disabled = true;
                    }
                    break;
                case 2: //Term-Term
                    for (let i = 0; i < this.resultOutputTypes.size; i++) {
                        if (i == 1 || i == 2 || i == 3 || i == 5) {
                            this.resultOutputTypes[i].disabled = true;
                        } else {
                            this.resultOutputTypes[i].disabled = false;
                        }
                    }
                    for (let i = 0; i < this.returnScopesOfPairs.size; i++) {
                        if (i == 2 || i == 3 || i == 4) {
                            this.returnScopesOfPairs[i].disabled = true;
                        } else {
                            this.returnScopesOfPairs[i].disabled = false;
                        }
                    }
                    break;
                case 3: //Term-Chunk
                case 4: //Chunk-Term
                    for (let i = 0; i < this.resultOutputTypes.size; i++) {
                        if (i == 1 || i == 4) {
                            this.resultOutputTypes[i].disabled = true;
                        } else {
                            this.resultOutputTypes[i].disabled = false;
                        }
                    }
                    for (let i = 0; i < this.returnScopesOfPairs.size; i++) {
                        if (i == 1 || i == 2) {
                            this.returnScopesOfPairs[i].disabled = true;
                        } else {
                            this.returnScopesOfPairs[i].disabled = false;
                        }
                    }
                    break;
                case 5: //Compose Query w/Terms
                case 6: //Compose Query w/Chunks
                    for (let i = 0; i < this.resultOutputTypes.size; i++) {
                        this.resultOutputTypes[i].disabled = true;
                    }
                    for (let i = 0; i < returnScopesOfPairs.size; i++) {
                        if (i == 1 || i == 2) {
                            this.returnScopesOfPairs[i].disabled = true;
                        } else {
                            this, (returnScopesOfPairs[i].disabled = false);
                        }
                    }
                    break;
                default:
                    for (let i = 0; i < this.resultOutputTypes.size; i++) {
                        this.resultOutputTypes[i].disabled = true;
                    }
                    for (let i = 0; i < returnScopesOfPairs.size; i++) {
                        this.returnScopesOfPairs[i].disabled = true;
                    }
            }
            if (
                this.searchConditions.step1Type > -1 &&
                this.searchConditions.step1Size > -1
            ) {
                this.nextDisabled = false;
            }
        },

        chunkSizeChosen: function () {
            if (
                this.searchConditions.step1Type > -1 &&
                this.searchConditions.step1Size > -1
            ) {
                this.nextDisabled = false;
            }
        },

        resultOutputTypeChosen: function () {
            // switch (searchConditions.step2) {
            //     case 1: //One Doc in Page Order
            //         returnScopesOfPairs[1].disabled = true
            //         returnScopesOfPairs[2].disabled = true
            //         break
            //     case 2: //
            //         if (searchConditions.step1)
            //         break
            //     default:
            // }

            // the method "outputTypeClick" and "scopeTypeClick" in the original lsa.js
            // (ll. 292-337) does not make sense to me.
            // They look like the case of choosing disabled buttons
            console.log("OK");
            if (this.searchConditions.step2 > -1) {
                this.nextDisabled = false;
            }
        },

        returnScopesOfPairChosen: function () {
            if (this.searchConditions.step3 > -1) {
                this.nextDisabled = false;
            }
        },
        runQuery: function () {
            //Running SQL query by sending HTTP requests.
        },
    },
    data() {
        return {
            labelBtnNext: "Next",
            currentStep: 1,
            nextDisabled: "next",
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
                { type: "Term-Chunk", disabled: false },
                { type: "Chunk-Term", disabled: false },
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
                { type: "Term Alpha Order", disabled: true },
                { type: "Doc Catalog Order", disabled: true },
                { type: "Graph for NWB", disabled: false },
                { type: "CSV: XY Term ↔ Doc", disabled: true },
            ],
            returnScopesOfPairs: [
                { scope: "All Above Chosen Value", disabled: false },
                { scope: "All Between Docs or Terms", disabled: false },
                { scope: "Within One Document (Doc-Doc)", disabled: false },
                { scope: "All w/Term Presence (Term ↔ Doc)", disabled: true },
                {
                    scope: "Only if Term Present (Term ↔ Doc)",
                    disabled: false,
                },
            ],
            documents: [],
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
