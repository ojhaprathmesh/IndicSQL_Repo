import { useRef, useState } from 'react'
import {
  ActivityIndicator,
  Keyboard,
  Platform,
  Pressable,
  ScrollView,
  StatusBar as NativeStatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ||
  (Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000')

const languageExamples = {
  English: 'Show PM-KISAN beneficiaries by state',
  Hindi: 'राज्य के अनुसार पीएम-किसान लाभार्थियों की संख्या दिखाएं',
  Bengali: 'রাজ্য অনুযায়ী পিএম-কিষাণ সুবিধাভোগীর সংখ্যা দেখান',
  Tamil: 'மாநில வாரியாக பிஎம் கிசான் பயனாளர்களின் எண்ணிக்கையைக் காட்டுங்கள்',
  Telugu: 'రాష్ట్రాల వారీగా పీఎం కిసాన్ లబ్ధిదారుల సంఖ్యను చూపించండి',
  Marathi: 'राज्यानुसार पीएम-किसान लाभार्थ्यांची संख्या दाखवा',
  Hinglish: 'State ke hisaab se PM-KISAN beneficiaries dikhao',
}

const languageByCode = {
  en: 'English',
  hi: 'Hindi',
  bn: 'Bengali',
  ta: 'Tamil',
  te: 'Telugu',
  mr: 'Marathi',
  'hi-en': 'Hinglish',
}

const answerCopy = {
  English: (count) => `Found ${count} ${count === 1 ? 'record' : 'records'}.`,
  Hindi: (count) => `${count} रिकॉर्ड मिले।`,
  Bengali: (count) => `${count}টি রেকর্ড পাওয়া গেছে।`,
  Tamil: (count) => `${count} பதிவுகள் கிடைத்தன.`,
  Telugu: (count) => `${count} రికార్డులు లభించాయి.`,
  Marathi: (count) => `${count} नोंदी मिळाल्या.`,
  Hinglish: (count) => `${count} records mile.`,
}

const titleCase = (value) =>
  value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())

const formatValue = (value) => {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') {
    return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(value)
  }
  return String(value)
}

export default function App() {
  const [selectedLanguage, setSelectedLanguage] = useState('English')
  const [query, setQuery] = useState(languageExamples.English)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const queryInput = useRef(null)

  const handleRunQuery = async () => {
    if (!query.trim()) {
      setError('Enter a question to search the data.')
      queryInput.current?.focus()
      return
    }

    Keyboard.dismiss()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() }),
      })
      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(data.detail || data.error || 'The request could not be completed.')
      }

      if (languageByCode[data.detected_language]) {
        setSelectedLanguage(languageByCode[data.detected_language])
      }
      setResult(data.execution_result || { columns: [], rows: [], row_count: 0 })
    } catch (requestError) {
      setError(requestError.message || 'Could not connect to the IndicSQL service.')
    } finally {
      setLoading(false)
    }
  }

  const handleNewQuestion = () => {
    setQuery('')
    setResult(null)
    setError('')
    queryInput.current?.focus()
  }

  const columns = result?.columns || []
  const rows = result?.rows || []
  const count = result?.row_count ?? rows.length

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View style={styles.brandIcon}>
            <Text style={styles.brandIconText}>B</Text>
          </View>
          <View style={styles.brandCopy}>
            <Text style={styles.brandKicker}>INDICSQL DATA EXPLORER</Text>
            <Text style={styles.brandName}>BharatQuery</Text>
          </View>
          <View style={styles.headerLeaf} />
        </View>

        <View style={styles.intro}>
          <Text style={styles.introKicker}>PUBLIC DATA, MADE ACCESSIBLE</Text>
          <Text style={styles.title}>Ask a question.{'\n'}Find an answer.</Text>
          <Text style={styles.subtitle}>
            Explore Indian public datasets in the language you’re comfortable with.
          </Text>
        </View>

        <View style={styles.searchCard}>
          <View style={styles.cardHeading}>
            <View>
              <Text style={styles.sectionEyebrow}>YOUR QUESTION</Text>
              <Text style={styles.sectionTitle}>What would you like to know?</Text>
            </View>
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.languageList}
          >
            {Object.keys(languageExamples).map((language) => {
              const selected = language === selectedLanguage
              return (
                <Pressable
                  key={language}
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                  onPress={() => {
                    setSelectedLanguage(language)
                    setQuery(languageExamples[language])
                    setError('')
                  }}
                  style={[styles.languageChip, selected && styles.languageChipSelected]}
                >
                  <Text style={[styles.languageChipText, selected && styles.languageChipTextSelected]}>
                    {language}
                  </Text>
                </Pressable>
              )
            })}
          </ScrollView>

          <TextInput
            ref={queryInput}
            accessibilityLabel={`Question in ${selectedLanguage}`}
            value={query}
            onChangeText={(text) => {
              setQuery(text)
              setError('')
            }}
            placeholder="Type your question here…"
            placeholderTextColor="#9AA49B"
            multiline
            textAlignVertical="top"
            returnKeyType="default"
            style={styles.questionInput}
          />

          {error ? (
            <View accessibilityRole="alert" style={styles.errorBox}>
              <Text style={styles.errorText}>{error}</Text>
              <Text style={styles.errorHint}>
                Check that the backend is running and reachable from this device.
              </Text>
            </View>
          ) : null}

          <Pressable
            accessibilityRole="button"
            onPress={handleRunQuery}
            disabled={loading}
            style={({ pressed }) => [
              styles.searchButton,
              pressed && !loading && styles.searchButtonPressed,
              loading && styles.searchButtonDisabled,
            ]}
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <>
                <Text style={styles.searchButtonText}>Search public data</Text>
                <Text style={styles.searchButtonArrow}>→</Text>
              </>
            )}
          </Pressable>
        </View>

        <View style={styles.resultsSection}>
          <View style={styles.resultsHeader}>
            <View>
              <Text style={styles.sectionEyebrow}>YOUR RESULTS</Text>
              <Text style={styles.resultsTitle}>Fetched data</Text>
            </View>
            {result ? (
              <View style={styles.countBadge}>
                <Text style={styles.countBadgeText}>
                  {count} {count === 1 ? 'record' : 'records'}
                </Text>
              </View>
            ) : null}
          </View>

          {result ? (
            <View style={styles.answerCard}>
              <Text style={styles.answerLanguage}>{selectedLanguage.toUpperCase()}</Text>
              <Text style={styles.answerText}>{answerCopy[selectedLanguage](count)}</Text>
              <View style={styles.answerDivider} />
              <Text style={styles.answerLanguage}>ENGLISH</Text>
              <Text style={styles.answerText}>{answerCopy.English(count)}</Text>
            </View>
          ) : null}

          {result && columns.length > 0 && rows.length > 0 ? (
            <View style={styles.recordList}>
              {rows.map((row, rowIndex) => {
                const headingColumn = columns.findIndex((column) =>
                  ['state_name', 'district_name', 'name', 'year', 'financial_year'].includes(
                    column.toLowerCase(),
                  ),
                )
                const heading = headingColumn >= 0 ? row[headingColumn] : `Record ${rowIndex + 1}`
                const details = columns
                  .map((column, columnIndex) => ({ column, value: row[columnIndex], columnIndex }))
                  .filter((item) => item.columnIndex !== headingColumn)

                return (
                  <View key={`record-${rowIndex}`} style={styles.recordCard}>
                    <View style={styles.recordHeadingRow}>
                      <Text style={styles.recordHeading}>{formatValue(heading)}</Text>
                      <Text style={styles.recordIndex}>{String(rowIndex + 1).padStart(2, '0')}</Text>
                    </View>
                    <View style={styles.recordDetails}>
                      {details.map(({ column, value, columnIndex }) => (
                        <View key={`${column}-${columnIndex}`} style={styles.recordDetail}>
                          <Text style={styles.recordLabel}>{titleCase(column)}</Text>
                          <Text style={styles.recordValue}>{formatValue(value)}</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                )
              })}
            </View>
          ) : result ? (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyTitle}>No matching records</Text>
              <Text style={styles.emptyText}>Try asking a different question.</Text>
            </View>
          ) : (
            <View style={styles.emptyCard}>
              <View style={styles.emptyIcon}>
                <Text style={styles.emptyIconText}>⌕</Text>
              </View>
              <Text style={styles.emptyTitle}>Your results will appear here</Text>
              <Text style={styles.emptyText}>
                Ask about public data to see clear, easy-to-read records.
              </Text>
            </View>
          )}

          {result ? (
            <Pressable
              accessibilityRole="button"
              onPress={handleNewQuestion}
              style={({ pressed }) => [styles.newQuestionButton, pressed && styles.newQuestionPressed]}
            >
              <Text style={styles.newQuestionText}>＋  Ask another question</Text>
            </Pressable>
          ) : null}
        </View>

        <Text style={styles.footer}>IndicSQL · Government data for everyone</Text>
      </ScrollView>
      <NativeStatusBar barStyle="dark-content" backgroundColor="#F5F7F2" />
    </View>
  )
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#F5F7F2',
    paddingTop: Platform.OS === 'android' ? NativeStatusBar.currentHeight || 0 : 0,
  },
  scrollContent: {
    width: '100%',
    maxWidth: 620,
    alignSelf: 'center',
    paddingHorizontal: 20,
    paddingBottom: 34,
  },
  header: {
    minHeight: 76,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#E8ECE5',
    marginBottom: 28,
  },
  brandIcon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E5EDE2',
    marginRight: 12,
  },
  brandIconText: {
    color: '#49644E',
    fontSize: 22,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Georgia' : 'serif',
  },
  brandCopy: {
    flex: 1,
  },
  brandKicker: {
    color: '#839083',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1.1,
  },
  brandName: {
    marginTop: 2,
    color: '#2F3D32',
    fontSize: 20,
    fontWeight: '700',
    letterSpacing: -0.5,
  },
  headerLeaf: {
    width: 10,
    height: 10,
    marginRight: 5,
    borderRadius: 5,
    backgroundColor: '#9BB49A',
  },
  intro: {
    marginBottom: 22,
  },
  introKicker: {
    color: '#738675',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.35,
    marginBottom: 10,
  },
  title: {
    color: '#2D3B31',
    fontSize: 34,
    lineHeight: 40,
    fontWeight: '700',
    letterSpacing: -1,
    fontFamily: Platform.OS === 'ios' ? 'Georgia' : 'serif',
  },
  subtitle: {
    maxWidth: 370,
    color: '#748076',
    fontSize: 14,
    lineHeight: 21,
    marginTop: 10,
  },
  searchCard: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E7EBE4',
    borderRadius: 18,
    padding: 18,
    shadowColor: '#445444',
    shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.045,
    shadowRadius: 14,
    elevation: 2,
  },
  cardHeading: {
    marginBottom: 15,
  },
  sectionEyebrow: {
    color: '#879387',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 5,
  },
  sectionTitle: {
    color: '#334136',
    fontSize: 17,
    fontWeight: '700',
  },
  languageList: {
    gap: 7,
    paddingBottom: 13,
  },
  languageChip: {
    minHeight: 34,
    justifyContent: 'center',
    paddingHorizontal: 12,
    borderRadius: 18,
    backgroundColor: '#F7F8F5',
    borderWidth: 1,
    borderColor: '#E7EBE4',
  },
  languageChipSelected: {
    backgroundColor: '#EAF0E8',
    borderColor: '#A8BBA7',
  },
  languageChipText: {
    color: '#6E7A70',
    fontSize: 12,
    fontWeight: '600',
  },
  languageChipTextSelected: {
    color: '#456148',
  },
  questionInput: {
    minHeight: 120,
    maxHeight: 190,
    paddingHorizontal: 13,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E1E6DE',
    backgroundColor: '#FCFDFC',
    color: '#364239',
    fontSize: 15,
    lineHeight: 22,
  },
  errorBox: {
    marginTop: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#EFD8D2',
    borderRadius: 10,
    backgroundColor: '#FFF8F5',
  },
  errorText: {
    color: '#984F43',
    fontSize: 13,
    fontWeight: '600',
  },
  errorHint: {
    color: '#9D766D',
    fontSize: 11,
    lineHeight: 16,
    marginTop: 4,
  },
  searchButton: {
    minHeight: 49,
    marginTop: 14,
    paddingHorizontal: 16,
    borderRadius: 11,
    backgroundColor: '#536E59',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchButtonPressed: {
    backgroundColor: '#435D49',
  },
  searchButtonDisabled: {
    opacity: 0.72,
  },
  searchButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  searchButtonArrow: {
    color: '#FFFFFF',
    fontSize: 19,
    marginLeft: 9,
    marginTop: -2,
  },
  resultsSection: {
    marginTop: 29,
  },
  resultsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  resultsTitle: {
    color: '#334136',
    fontSize: 22,
    fontWeight: '700',
    letterSpacing: -0.4,
  },
  countBadge: {
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: 16,
    backgroundColor: '#EAF0E8',
  },
  countBadgeText: {
    color: '#536E59',
    fontSize: 11,
    fontWeight: '700',
  },
  answerCard: {
    padding: 15,
    marginBottom: 13,
    borderWidth: 1,
    borderColor: '#E5EBE2',
    borderRadius: 13,
    backgroundColor: '#FAFCF9',
  },
  answerLanguage: {
    color: '#879387',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 4,
  },
  answerText: {
    color: '#48564A',
    fontSize: 14,
    lineHeight: 20,
  },
  answerDivider: {
    height: 1,
    marginVertical: 11,
    backgroundColor: '#E7ECE4',
  },
  recordList: {
    gap: 10,
  },
  recordCard: {
    padding: 15,
    borderWidth: 1,
    borderColor: '#E7EBE4',
    borderRadius: 13,
    backgroundColor: '#FFFFFF',
  },
  recordHeadingRow: {
    minHeight: 27,
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingBottom: 9,
    borderBottomWidth: 1,
    borderBottomColor: '#EFF1ED',
  },
  recordHeading: {
    flex: 1,
    color: '#36453A',
    fontSize: 15,
    fontWeight: '700',
    marginRight: 10,
  },
  recordIndex: {
    color: '#A1AAA1',
    fontSize: 10,
    fontWeight: '700',
  },
  recordDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    rowGap: 12,
    columnGap: 14,
    paddingTop: 12,
  },
  recordDetail: {
    minWidth: '43%',
    flexGrow: 1,
  },
  recordLabel: {
    color: '#879187',
    fontSize: 10,
    marginBottom: 3,
  },
  recordValue: {
    color: '#455248',
    fontSize: 13,
    fontWeight: '600',
  },
  emptyCard: {
    minHeight: 154,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 22,
    borderWidth: 1,
    borderColor: '#E7EBE4',
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.65)',
  },
  emptyIcon: {
    width: 38,
    height: 38,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 13,
    backgroundColor: '#EAF0E8',
    marginBottom: 10,
  },
  emptyIconText: {
    color: '#68806B',
    fontSize: 24,
    lineHeight: 29,
  },
  emptyTitle: {
    color: '#47554A',
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'center',
  },
  emptyText: {
    maxWidth: 270,
    color: '#89938A',
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
    marginTop: 5,
  },
  newQuestionButton: {
    minHeight: 45,
    marginTop: 13,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#CCD8CA',
    borderRadius: 11,
    backgroundColor: '#F8FAF6',
  },
  newQuestionPressed: {
    backgroundColor: '#EEF3EC',
  },
  newQuestionText: {
    color: '#526D57',
    fontSize: 13,
    fontWeight: '700',
  },
  footer: {
    paddingTop: 25,
    color: '#9AA39A',
    fontSize: 10,
    textAlign: 'center',
  },
})
