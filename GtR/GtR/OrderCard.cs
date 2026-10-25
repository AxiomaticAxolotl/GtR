namespace GtR
{
    public class OrderCard
    {
        public CardSuit CardSuit { get; set; }
        public string CardName { get; set; }
        public string CardText { get; set; }
        public CardSet CardSet { get; set; }
        public bool ImageIsRoughlyCentered { get; set; }

        //Optional per-card override for the card text size, in the same units as orderCardTextFontSizeInPoints.
        //Only needed for the handful of cards whose text is too long to fit the box at the standard size.
        public float? CardTextFontSizeInPoints { get; set; }
    }
}
